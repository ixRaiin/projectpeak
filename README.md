# ProjectPeak

ProjectPeak is a lightweight project management and costing tool tailored for **construction businesses, local organizations, and community groups**. It balances essential project management features with a simplified, user-friendly interface — making structured project workflows accessible without the complexity of enterprise software.

---

## 📑 Table of Contents

1. [Features](#-features)
2. [Tech Stack](#-tech-stack)
3. [Repository Structure](#-repository-structure)
4. [Getting Started](#-getting-started)
   * [Backend Setup](#backend-setup)
   * [Frontend Setup](#frontend-setup)
5. [API Highlights](#-api-highlights)
6. [Testing](#-testing)
7. [Roadmap](#-roadmap)
8. [Developer Guide](#-developer-guide)
   * [Conventions](#conventions)
   * [Migrations](#migrations)
   * [Seeding Test Data](#seeding-test-data)
   * [Common Pitfalls](#common-pitfalls)
   * [Development Patterns](#development-patterns)
9. [License](#-license)
10. [📖 Full Technical Documentation](./DOCUMENTATION.md)

---

## ✨ Features

* **Projects** — Create, manage, and track projects with progress updates
* **Tasks** — Nested subtasks, statuses (`todo / in_progress / done`), and progress bar
* **Expenses** — Real-time expense entry with line items, vendors, and automatic totals
* **Dashboard** — Overview of active projects, financials, and KPIs
* **Clients & Catalog** — Manage clients, categories, and components with flexible integration
* **Hybrid Methodology** — Agile for iterative software dev; Waterfall for structured construction phases

---

## 🛠️ Tech Stack

**Backend**

* Python 3.11+
* Flask + Flask-SQLAlchemy + Alembic (migrations)
* SQLite (lightweight dev database)
* Token-based authentication

**Frontend**

* Vue 3 (Composition API)
* Pinia (state management)
* Vue Router 4
* Vite (bundler / dev server)
* TailwindCSS (utility-first styling)

---

## 📂 Repository Structure

```
projectpeak/
├─ backend/
│  ├─ app.py            # Flask app factory
│  ├─ models.py         # SQLAlchemy models
│  ├─ projects.py       # /api/projects endpoints
│  ├─ expenses.py       # /api/projects/:pid/expenses endpoints
│  ├─ tasks.py          # /api/projects/:pid/tasks endpoints
│  ├─ migrations/       # Alembic migrations
│  └─ instance/projectpeak.db
└─ frontend/
   ├─ src/
   │  ├─ router/        # Vue Router config
   │  ├─ stores/        # Pinia stores
   │  ├─ views/         # Page components
   │  └─ lib/api.js     # API client
```

---

## 🚀 Getting Started

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

mkdir -p instance
flask --app app db stamp head
flask --app app db migrate -m "init"
flask --app app db upgrade

flask --app app run --debug
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access:

* Backend → `http://127.0.0.1:5000/api`
* Frontend → `http://localhost:5173`

---

## 🔑 API Highlights

* `POST /api/login` → Authenticate, returns token
* `GET /api/projects` → List all projects
* `POST /api/projects/:pid/tasks` → Create a new task
* `POST /api/projects/:pid/expenses` → Add an expense (`expense_date: YYYY-MM-DD`)
* `GET /api/projects/:pid/summary` → Planned vs actual costs

👉 For the **full API reference**, see:
📖 [Full Technical Documentation](./DOCUMENTATION.md#5-api-reference)

---

## 🧪 Testing

* **Unit Tests** — Validate API endpoints (Flask)
* **System Tests** — Verify frontend–backend integration
* **User Acceptance Tests (UAT)** — End-user validation in realistic workflows

---

## 📈 Roadmap

* ✅ Core project / task / expense management
* ✅ Expense editing, totals, and page
* ✅ Nested task UI (drag-drop ordering, inline edit)
* 🔮 AI-powered insights for budgets & automation
* 🔮 Mobile-friendly responsive UI
* 🔮 Open-source community extensions

---

## 👨‍💻 Developer Guide

### Conventions

* **API base path:** `/api`
* **Dates:** Always `YYYY-MM-DD`
* **Currency:** USD, format with `Intl.NumberFormat`
* **Auth:** Bearer token in `Authorization` header
* **Imports:**

  ```js
  import api from '@/lib/api'
  await api.get('/projects')
  ```
* **Named routes:**

  ```js
  { path: '/projects/:id', name: 'project-detail', component: ProjectDetailView }
  ```

### Migrations

```bash
flask --app app db migrate -m "sync models"
flask --app app db upgrade
```

ℹ️ SQLite: avoid dropping unnamed constraints; always use additive migrations.

### Seeding Test Data

```bash
flask --app app shell
```

```python
from backend.models import db, Client, Project, Category

c = Client(name="Demo Client", contact_name="John Doe", email="john@example.com")
db.session.add(c); db.session.commit()

p = Project(client_id=c.id, code="PP-0001", name="Demo Project", status="planned")
db.session.add(p); db.session.commit()

cat1 = Category(name="Materials", description="Construction raw materials")
cat2 = Category(name="Labor", description="Workforce costs")
db.session.add_all([cat1, cat2]); db.session.commit()
```

### Common Pitfalls

1. Import `api` as default, not `{ api }`.
2. Send valid dates (`YYYY-MM-DD`), reject empty.
3. File names must match exactly (`ProjectDetailView.vue`).
4. Keep task routes only in `tasks.py`.

### Development Patterns

* Stores thin, all network via `api.js`
* Tasks returned flat, grouped into tree in frontend
* Expenses validated server-side
* Progress computed on backend (`/tasks/progress`)

---

## 📜 License

This project is developed for academic and professional purposes. Licensing terms will be clarified in future open-source releases.

---

## 📖 Full Documentation

See the full technical deep dive:
👉 [DOCUMENTATION.md](./DOCUMENTATION.md)

---
