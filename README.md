# 🚀 Projeto Orizon — Gerenciador de Tarefas Inteligente

[![Backend CI](https://github.com/techcarlosandre/Orizon/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/techcarlosandre/Orizon/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/techcarlosandre/Orizon/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/techcarlosandre/Orizon/actions/workflows/frontend-ci.yml)

> Uma aplicação web de gerenciamento de tarefas profissional e de alto desempenho. Construída sob as melhores práticas de **Clean Code**, **Testes Automatizados (98% de cobertura)** e infraestrutura robusta na **AWS** com **SSL/HTTPS**.

---

## 🔗 Links do Projeto
* **Deploy Ativo (AWS):** [https://orizon.techcarlos.com.br](https://orizon.techcarlos.com.br)
* **Desenvolvedor:** [Carlos Silva (GitHub)](https://github.com/techcarlosandre)

---

## 🏗️ Visão Geral da Arquitetura

O **Projeto Orizon** adota uma separação clara de responsabilidades (Decoupled Architecture) utilizando Django REST Framework no backend e React no frontend, orquestrados via containers Docker.

```mermaid
graph TD
    Client[Cliente / Navegador] -->|HTTPS :443 / HTTP :80| Nginx[Nginx Reverse Proxy]
    Nginx -->|Arquivos Estáticos| React[React SPA Frontend]
    Nginx -->|API Proxy /api/| Django[Django Backend API]
    Django -->|ORM| PostgreSQL[PostgreSQL Database]
    Django -.->|HTTP Client| ExternalAPI[Suggestions Microservice]
```

### 🛠️ Tecnologias Utilizadas
* **Backend:** Python 3.12, Django 5.0, Django REST Framework, JWT (SimpleJWT), Gunicorn.
* **Frontend:** React 18, Vite 5, Axios (com interceptores de refresh token automático), Vanilla CSS.
* **Banco de Dados:** PostgreSQL 16 (Alpine).
* **Infraestrutura & DevOps:** AWS EC2, Docker & Docker Compose, Nginx, Let's Encrypt (Certbot), GitHub Actions.
* **Qualidade & Testes:** pytest (unitário/integração com 98% de cobertura), Selenium Webdriver (E2E com Chrome Headless).

---

## ⚡ Principais Funcionalidades

1. **Autenticação JWT Segura:** Login, registro e renovação transparente de sessão utilizando *Refresh Tokens* com sistema de blacklist.
2. **Gerenciamento de Tarefas completo (CRUD):** Criação, edição, listagem com paginação e exclusão de tarefas personalizadas.
3. **Categorias Inteligentes:** Organização de tarefas com sugestões automáticas baseadas em termos (ex: "estudar" sugere a categoria "Estudos").
4. **Compartilhamento Granular (TaskShare):** Compartilhe tarefas específicas com outros usuários da plataforma definindo níveis de permissão exclusivos (`view` ou `edit`).

---

## 🔬 Qualidade de Código & Cobertura de Testes

A qualidade do projeto é garantida por uma robusta suíte com mais de 100 testes automatizados, integrados em um pipeline de Integração Contínua (CI) no GitHub Actions.

### Cobertura de Testes do Backend (98%)
```text
Name                                                                                       Stmts   Miss  Cover
------------------------------------------------------------------------------------------------------------------------
backend/apps/accounts/models.py                                                                7      1    86%
backend/apps/accounts/serializers.py                                                          26      0   100%
backend/apps/accounts/views.py                                                                56      2    96%
backend/apps/suggestions/client.py                                                            27      0   100%
backend/apps/suggestions/service.py                                                           15      0   100%
backend/apps/tasks/models.py                                                                  57      3    95%
backend/apps/tasks/serializers.py                                                             73      2    97%
backend/apps/tasks/views.py                                                                   76      0   100%
------------------------------------------------------------------------------------------------------------------------
TOTAL                                                                                        466      8    98%
```

### Testes Fim a Fim (E2E) com Selenium
Os testes simulando a jornada real do usuário (Registro -> Login -> Criar Categoria -> Criar Tarefa -> Concluir -> Logout) rodam de forma automatizada em modo headless (sem interface gráfica), tanto localmente quanto no ambiente de CI do GitHub Actions.

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
* Docker e Docker Compose instalados.

### 1. Clonar o Repositório e Configurar Env
```bash
git clone https://github.com/techcarlosandre/Orizon.git
cd Orizon
cp .env.example .env
```

### 2. Iniciar a Aplicação com Docker Compose (Desenvolvimento)
```bash
docker compose up --build
```
* **Frontend:** `http://localhost:5173`
* **API Backend:** `http://localhost:8000/api/`

### 3. Executar a Suíte de Testes
```bash
# Rodar testes unitários e de integração (Django + pytest)
docker compose exec backend pytest -v

# Rodar testes E2E (Selenium)
cd selenium_tests
pip install -r requirements.txt
pytest test_e2e.py -v
```

---

## 🧠 Decisões de Design (Clean Code)
* **ViewSets & Routers (DRF):** DRY (*Don't Repeat Yourself*) levado ao máximo na estruturação das APIs.
* **Segurança declarativa de permissões:** Criação de mapeamentos específicos para as permissões customizadas de compartilhamento.
* **Isolamento de Domínio:** A lógica de sugestão de categorias está isolada na pasta `suggestions/` e é consumida via cliente HTTP encapsulado (`httpx`), permitindo sua fácil migração para microsserviços futuros.
* **Flat Config (ESLint):** Configuração moderna de linting no frontend para garantir conformidade estrita de estilo de código.

---

## 📄 Licença
Este projeto é de código aberto sob os termos da licença [MIT](LICENSE).
