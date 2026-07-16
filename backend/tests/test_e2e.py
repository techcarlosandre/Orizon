"""
E2E tests using Selenium (Chrome Headless).

This module validates the complete user journey:
1. Register a new user
2. Login
3. Add a Category
4. Add a Task using that category
5. Toggle task completion
6. Logout

Infrastructure:
- Automatically builds the React frontend.
- Spawns a background thread to serve the static frontend bundle.
- Uses django's live_server for the actual REST API.
- Configures Chrome in headless mode for seamless CI execution.
"""
import os
import subprocess
import threading
import http.server
import socketserver
import time
import pytest
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

User = get_user_model()


# ── Frontend Background Server Fixture ────────────────────────────────────────

class ThreadedHTTPServer(object):
    """Serve a directory on a background thread."""
    def __init__(self, directory, port=3000):
        self.directory = directory
        self.port = port
        self.server = None
        self.thread = None

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

            def do_GET(self):
                # SPA Fallback: If path does not map to a real file, serve index.html
                path_on_disk = self.translate_path(self.path)
                if not os.path.exists(path_on_disk) and not self.path.startswith("/assets/"):
                    self.path = "/index.html"
                return super().do_GET()

        self.Handler = Handler

    def start(self):
        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer(("", self.port), self.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


@pytest.fixture(scope="function")
def frontend_server(live_server):
    """
    Build React app and serve its bundle on port 3000.
    Ensures VITE_API_BASE_URL points to the dynamic live_server endpoint.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frontend_dir = os.path.join(root_dir, "frontend")
    dist_dir = os.path.join(frontend_dir, "dist")

    # 1. Build frontend targeting the dynamic live_server URL
    env = os.environ.copy()
    env["VITE_API_BASE_URL"] = f"{live_server.url}/api"
    
    print(f"\nBuilding frontend targeting dynamic API: {live_server.url}/api ...")
    # Run npm build synchronously
    subprocess.run(
        "npm run build",
        shell=True,
        cwd=frontend_dir,
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 2. Start serving the dist/ folder on port 3000
    server = ThreadedHTTPServer(dist_dir, port=3000)
    server.start()
    time.sleep(1)  # Let it bind

    yield "http://localhost:3000"

    server.stop()


# ── Webdriver Fixture ─────────────────────────────────────────────────────────

@pytest.fixture
def driver():
    """Headless Chrome driver initialized with safe CI/Docker options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    
    yield driver
    
    driver.quit()


# ── E2E Test Suite ────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestE2EFlow:
    def test_complete_user_flow(self, live_server, frontend_server, driver):
        """
        Verify the full integration flow:
        Register -> Login -> Create Cat -> Create Task -> Toggle -> Logout
        """
        try:
            # 1. Visit Register Page
            driver.get(f"{frontend_server}/register")
            
            # Wait for form input element to be present instead of emoji text matching
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Fill registration form
            driver.find_element(By.ID, "username").send_keys("e2e_user")
            driver.find_element(By.ID, "email").send_keys("e2e_user@example.com")
            driver.find_element(By.ID, "firstName").send_keys("E2E")
            driver.find_element(By.ID, "lastName").send_keys("Tester")
            driver.find_element(By.ID, "password").send_keys("Password123!")
            driver.find_element(By.ID, "passwordConfirm").send_keys("Password123!")
            
            # Submit
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            # Should be redirected to Dashboard ("Bem-vindo, E2E!")
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element((By.CLASS_NAME, "dashboard-title"), "Bem-vindo, E2E!")
            )

            # 2. Create Category
            # Open categories modal
            btn_cat = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Categorias')]"))
            )
            btn_cat.click()
            
            # Wait for Modal input field to be present
            cat_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content input[placeholder='Nova categoria']"))
            )

            # Add new category
            cat_input.send_keys("E2E Trabalho")
            driver.find_element(By.CSS_SELECTOR, ".modal-content form button[type='submit']").click()

            # Verify category appears in list
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='E2E Trabalho']"))
            )

            # Close Modal
            driver.find_element(By.XPATH, "//button[text()='Fechar']").click()

            # 3. Create Task
            # Open Task Modal
            driver.find_element(By.XPATH, "//button[contains(text(), '+ Nova Tarefa')]").click()
            
            # Wait for Task Modal title input field
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "task-title"))
            )

            # Fill title and description
            driver.find_element(By.ID, "task-title").send_keys("Reuniao E2E")
            driver.find_element(By.ID, "task-description").send_keys("Descricao da tarefa E2E")
            
            # Select Category
            select_el = driver.find_element(By.ID, "task-category")
            for option in select_el.find_elements(By.TAG_NAME, "option"):
                if option.text == "E2E Trabalho":
                    option.click()
                    break

            # Save Task
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            # Verify task is created and displayed in dashboard
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Reuniao E2E']"))
            )

            # 4. Toggle Task Status
            task_card = driver.find_element(By.CLASS_NAME, "task-card")
            indicator = task_card.find_element(By.CLASS_NAME, "status-indicator")
            
            # Initially pending
            assert "pending" in indicator.get_attribute("class")

            # Click Complete button
            task_card.find_element(By.XPATH, ".//button[text()='✓']").click()

            # Should change to completed indicator
            WebDriverWait(driver, 5).until(
                lambda d: "completed" in indicator.get_attribute("class")
            )

            # 5. Logout
            driver.find_element(By.XPATH, "//button[text()='Sair']").click()

            # Redirected back to login - wait for login password input
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            assert "/login" in driver.current_url

        except Exception as exc:
            print("\n=== E2E FAILURE: PAGE SOURCE ===")
            # Encodagem segura para evitar erros de charmap cp1252 no terminal Windows com Emojis
            safe_html = driver.page_source[:5000].encode('ascii', errors='ignore').decode('ascii')
            print(safe_html)
            print("\n=== E2E FAILURE: BROWSER CONSOLE LOGS ===")
            try:
                for entry in driver.get_log('browser'):
                    print(entry)
            except Exception as log_err:
                print("Could not retrieve browser logs:", log_err)
            raise exc
