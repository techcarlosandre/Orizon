# Orizon — To-Do List Avançado

> Aplicação web de gerenciamento de tarefas com autenticação JWT, compartilhamento, categorias, filtros e API externa de sugestões.

---

## 🚀 Rodando o projeto

### Pré-requisitos
- Docker ≥ 24 e Docker Compose ≥ 2.20

### 1. Clone e configure as variáveis de ambiente

```bash
git clone https://github.com/SEU_USUARIO/orizon.git
cd orizon
cp .env.example .env
# Edite .env com os valores desejados
```

### 2. Suba todos os serviços

```bash
docker compose up --build
```

| Serviço    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:5173        |
| Backend API | http://localhost:8000/api/  |
| Django Admin | http://localhost:8000/admin/ |
| PostgreSQL  | localhost:5432               |

### 3. Sem Docker (desenvolvimento local)

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Configure as variáveis (use um .env ou exporte manualmente)
export DJANGO_SECRET_KEY="dev-secret"
export DJANGO_SETTINGS_MODULE="config.settings.development"
export POSTGRES_HOST=localhost   # ou use SQLite temporariamente

python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Rodando os testes

### Testes de backend (pytest)

```bash
# Com Docker
docker compose exec backend pytest -v

# Sem Docker (dentro do venv, na pasta /backend)
pytest -v
```

### Testes E2E com Selenium

```bash
# Pré-requisitos: Chrome instalado + ChromeDriver no PATH
# Os serviços devem estar rodando (docker compose up)

cd selenium_tests
pip install selenium pytest
pytest test_e2e.py -v
```

---

## 🏗 Arquitetura da aplicação

```
orizon/
├── backend/              ← Django 5 + DRF
│   ├── config/           ← settings (base/dev/prod), urls, wsgi
│   ├── apps/
│   │   ├── accounts/     ← Auth: registro, login, logout (JWT)
│   │   ├── tasks/        ← CRUD: Task, Category, TaskShare
│   │   └── suggestions/  ← API externa própria (sugestão de categoria)
│   └── tests/            ← pytest (unit + integration)
├── frontend/             ← React 18 + Vite 5
│   └── src/
│       ├── api/          ← Axios + interceptors JWT
│       ├── components/   ← Componentes reutilizáveis
│       ├── hooks/        ← useTasks, useAuth, useCategories
│       └── pages/        ← Login, Register, Dashboard, TaskDetail
├── selenium_tests/       ← E2E com Selenium + Chrome headless
├── .github/workflows/    ← CI: backend-ci.yml, frontend-ci.yml
├── docker-compose.yml    ← Dev (hot-reload)
└── docker-compose.prod.yml ← Produção (Coolify)
```

### Camadas do backend

```
Request → URL Router → ViewSet → Permission → Serializer → Model → PostgreSQL
                            ↓
                      FilterBackend (django-filter)
                            ↓
                      Pagination (PageNumberPagination)
```

---

## 🗄 Modelos de dados

### Task
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID | PK auto-gerado |
| title | CharField(255) | — |
| description | TextField | optional |
| category | FK → Category | nullable |
| status | choices: pending/completed | — |
| due_date | DateField | optional |
| owner | FK → User | — |

### TaskShare — Regra de permissão
| Permissão | Pode ver | Pode editar | Pode marcar concluída | Pode excluir/compartilhar |
|-----------|----------|-------------|----------------------|--------------------------|
| `view` | ✅ | ❌ | ✅ | ❌ |
| `edit` | ✅ | ✅ | ✅ | ❌ |
| owner | ✅ | ✅ | ✅ | ✅ |

---

## ⚙️ Variáveis de ambiente

Ver [.env.example](./.env.example) para a lista completa.

---

## 🧠 Decisões de design

| Decisão | Justificativa |
|---------|---------------|
| **JWT via simplejwt** | Stateless, padrão da indústria, suporte a refresh + blacklist |
| **UUID como PK** | Evita enumeração de recursos na URL |
| **`view` / `edit` no TaskShare** | Granularidade adequada ao domínio, simples de testar |
| **`suggestions` como app Django separado** | Cumpre o requisito de "API externa própria" sem overhead de infra extra; pode ser extraído como microserviço no futuro |
| **`httpx` para consumo interno** | API moderna, async-ready, fácil de mockar com `respx` nos testes |
| **`django-filter`** | Integração nativa com DRF, declarativo, testável sem boilerplate |
| **ViewSets + DefaultRouter** | DRY máximo — CRUD automático + custom actions (`toggle_status`, `share`) |
| **Multi-stage Dockerfile** | Dev com hot-reload, prod otimizado (sem ferramentas de build) |
| **Coolify + docker-compose.prod.yml** | Separação clara dev/prod, compatível com deploy via Coolify |

---

## 📄 Licença

MIT
