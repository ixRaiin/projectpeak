# ProjectPeak – Documentation

## 📑 Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [System Architecture](#system-architecture)
4. [Database Schema](#database-schema)
5. [API Reference](#api-reference)
6. [Frontend Integration](#frontend-integration)
7. [Known Issues & Fixes](#known-issues--fixes)
8. [Conventions](#conventions)
9. [Roadmap](#roadmap)
10. [Developer Setup](#developer-setup)

---

## 1. Overview

**ProjectPeak** is a **construction-oriented project management platform** that unifies client, project, task, expense, and catalog tracking into one system.

It is designed for **construction companies and project managers**, but flexible enough for broader use cases.

---

## 2. Core Features

* **Clients** – Manage client information and contacts.
* **Projects** – Budgets, codes (auto-generated), timelines, and client links.
* **Tasks** – Subtasks, statuses (`todo`, `in_progress`, `done`), assignees, due dates, and progress %.
* **Expenses** – Vendor-linked expenses, auto reference numbers (`INV-####`), multi-line entries.
* **Catalog** – Vendors → Categories → Components with pricing & units.
* **Reports** – Budget vs. Actuals, task completion progress.

---

## 3. System Architecture

### Backend

* **Flask + SQLAlchemy + Alembic** (SQLite for dev)
* **Blueprints**: `projects.py`, `expenses.py`, `tasks.py`, `auth.py`
* **Auth**: Token-based (`_get_token_from_request`, `_verify_token`)

### Frontend

* **Vue 3 + Vite**
* **Pinia** for state
* **Vue Router** with named routes
* **TailwindCSS** for styling
* **API Layer**: `src/lib/api.js` (default export: `.get/.post/.patch/.delete`)

---

## 4. Database Schema

### Projects

```sql
projects (
  id INTEGER PRIMARY KEY,
  client_id INTEGER REFERENCES clients(id),
  code TEXT UNIQUE,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'planned',
  budget_amount_usd NUMERIC,
  currency TEXT DEFAULT 'USD',
  start_date DATE,
  end_date DATE,
  created_at DATETIME,
  updated_at DATETIME
)
```

### Expenses

```sql
expenses (
  id INTEGER PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  reference_no TEXT UNIQUE,  -- auto INV-####
  vendor TEXT,
  expense_date DATE,
  note TEXT
)

expense_lines (
  id INTEGER PRIMARY KEY,
  expense_id INTEGER REFERENCES expenses(id),
  category_id INTEGER,
  component_id INTEGER,
  quantity NUMERIC,
  unit_price_usd NUMERIC,
  line_total_usd NUMERIC
)
```

### Tasks

```sql
tasks (
  id INTEGER PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  parent_task_id INTEGER REFERENCES tasks(id),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT CHECK(status IN ('todo','in_progress','done')),
  assignee_user_id INTEGER,
  due_date DATE,
  order_index INTEGER
)

task_comments (
  id INTEGER PRIMARY KEY,
  task_id INTEGER REFERENCES tasks(id),
  user_id INTEGER,
  body TEXT,
  created_at DATETIME
)
```

### Catalog

```sql
categories (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT
)

components (
  id INTEGER PRIMARY KEY,
  category_id INTEGER REFERENCES categories(id),
  name TEXT NOT NULL,
  unit_price_usd NUMERIC,
  unit_of_measure TEXT
)
```

---

## 5. API Reference

### Projects

* `GET /api/projects` → list projects
* `GET /api/projects/:id/summary` → budget vs actual

### Expenses

* `GET /api/projects/:id/expenses` → list expenses
* `POST /api/projects/:id/expenses`

  ```json
  {
    "expense_date": "2025-08-28",
    "vendor": "ACME Materials",
    "note": "Purchase of cement",
    "lines": [
      { "category_id": 1, "component_id": 2, "quantity": 10, "unit_price_usd": 12.5 }
    ]
  }
  ```

### Tasks

* `GET /api/projects/:pid/tasks` → list tasks
* `POST /api/projects/:pid/tasks` → create task
* `PATCH /api/projects/:pid/tasks/:tid` → update task
* `DELETE /api/projects/:pid/tasks/:tid` → delete task
* `GET /api/projects/:pid/tasks/progress` → task completion %

### Catalog

* `GET /api/catalog` → list vendors, categories, components
* `POST /api/catalog/categories` → add category
* `POST /api/catalog/components` → add component

---

## 6. Frontend Integration

### API Helper

```js
import api from '@/lib/api'
const projects = await api.get('/projects')
```

⚠️ Always use **default import**, not `{ api }`.

### Router

```vue
<RouterLink :to="{ name: 'project-detail', params:{ id: project.id } }">
  View
</RouterLink>
```

### Stores

* `projects.js` → manages project state
* `expenses.js` → normalizes line items, computes totals
* `tasks.js` → handles nested tasks, computes progress

---

## 7. Known Issues & Fixes

### SQLite “readonly database”

```bash
chmod 664 instance/projectpeak.db
```

or recreate DB with migrations.

### Dates

* Must be sent as `YYYY-MM-DD` from frontend.

### Alembic

* Always run:

```bash
flask --app app db stamp head
flask --app app db migrate -m "sync models"
flask --app app db upgrade
```

### Router import errors

* Ensure:

  ```js
  export default api
  ```

  and use:

  ```js
  import api from '@/lib/api'
  ```

### Expense form bug

* Ensure `.quantity` is bound with `.number` modifier:

  ```vue
  <input v-model.number="line.quantity" type="number" />
  ```

---

## 8. Conventions

* **Dates**: `YYYY-MM-DD` only.
* **API imports**: `import api from '@/lib/api'`.
* **Routes**: always use `name: 'project-detail'`.
* **Migrations**: additive changes only (SQLite limitation).
* **UI**: minimalist (navy + subtle red).

---

## 9. Roadmap

* **Now**: Expense edit/delete, task drag-drop ordering.
* **Next**: Dashboard sidebar panels, minimalist redesign, new fonts.
* **Later**: Pagination, attachment system, vendor-specific catalog.

---

## 10. Developer Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app db upgrade
flask --app app run
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---
