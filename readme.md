# 🌐 TaskSphere — Real-Time Collaborative Task Management

> A professional full-stack web application with real-time collaboration, Kanban boards, drag-and-drop, charts, team management and more.

---

## ✨ Feature Overview

| Feature | Details |
|---|---|
| **Auth** | Register, Login, Logout, Bcrypt hashing, Flask sessions |
| **Dashboard** | Animated stat cards, Chart.js trends, doughnut charts, live activity feed |
| **Projects** | CRUD, color tags, deadline, progress bar, team members |
| **Tasks** | Full CRUD, priority, status, assignee, deadline, comments, bulk actions |
| **Kanban** | Drag & Drop between To Do / In Progress / Completed, real-time sync |
| **Calendar** | Monthly view with task & project deadlines highlighted |
| **Team** | Member cards, workload stats, per-member task breakdown |
| **Profile** | Edit bio, preferences, dark mode toggle, activity log |
| **Real-time** | Socket.IO notifications, live activity feed, typing indicators |
| **Extras** | Global search, dark/light mode, confetti on task complete, keyboard shortcuts |

---

## 🛠 Tech Stack

```
Backend  : Python 3.11 · Flask 3.0 · Flask-SocketIO · Flask-PyMongo · Flask-Bcrypt
Database : MongoDB 6+ (local: mongodb://localhost:27017/tasksphere)
Frontend : Vanilla JS · Socket.IO client · Chart.js 4 · AOS animations
Fonts    : Syne (headings) · DM Sans (body)  — Google Fonts
Icons    : Font Awesome 6
Real-time: eventlet async worker
```

---

## 📁 Folder Structure

```
tasksphere/
├── app.py                    ← Flask app, routes, Socket.IO events
├── requirements.txt          ← Python dependencies
├── seed_data.py              ← Demo data seeder
│
├── models/
│   └── schemas.py            ← MongoDB schema, indexes, aggregation pipelines
│
├── static/
│   ├── css/
│   │   └── style.css         ← Master stylesheet (3200+ lines)
│   ├── js/
│   │   ├── app.js            ← Core: socket init, modals, search, toasts, helpers
│   │   ├── extras.js         ← Charts helpers, confetti, ripples, scroll-to-top
│   │   └── realtime.js       ← Socket.IO event manager class
│   ├── images/               ← (place assets here)
│   └── uploads/              ← File attachment storage
│
└── templates/
    ├── base.html             ← Sidebar, topbar, loader layout
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── projects.html
    ├── tasks.html
    ├── kanban.html
    ├── calendar.html
    ├── team.html
    └── profile.html
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- MongoDB running locally on port 27017
- pip

### 2. Clone & Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Start MongoDB

```bash
# macOS (homebrew)
brew services start mongodb-community

# Ubuntu/Debian
sudo systemctl start mongod

# Windows — run in a separate terminal:
mongod --dbpath C:\data\db
```

### 4. Seed Demo Data (optional but recommended)

```bash
python seed_data.py
```

This creates **5 demo users**, 5 projects, 26 tasks, comments, notifications, and activity logs.

**Demo credentials (all use password: `Password123!`)**

| Role    | Email                    |
|---------|--------------------------|
| Admin   | alice@tasksphere.io      |
| Manager | bob@tasksphere.io        |
| Member  | carol@tasksphere.io      |
| Member  | david@tasksphere.io      |
| Manager | eva@tasksphere.io        |

### 5. Run the App

```bash
python app.py
```

Open: **http://localhost:5000**

---

## 🔑 API Reference

### Auth

| Method | Endpoint     | Description            |
|--------|--------------|------------------------|
| POST   | `/register`  | Create new account     |
| POST   | `/login`     | Authenticate user      |
| GET    | `/logout`    | End session            |

### Dashboard

| Method | Endpoint          | Description                        |
|--------|-------------------|------------------------------------|
| GET    | `/api/dashboard`  | Stats, charts, activity, notifs    |

### Projects

| Method | Endpoint                    | Description            |
|--------|-----------------------------|------------------------|
| GET    | `/api/projects`             | List all projects      |
| POST   | `/api/projects`             | Create project         |
| GET    | `/api/projects/<id>`        | Get single project     |
| PUT    | `/api/projects/<id>`        | Update project         |
| DELETE | `/api/projects/<id>`        | Delete project + tasks |

### Tasks

| Method | Endpoint                         | Description                    |
|--------|----------------------------------|--------------------------------|
| GET    | `/api/tasks`                     | List tasks (with filters)      |
| POST   | `/api/tasks`                     | Create task                    |
| GET    | `/api/tasks/<id>`                | Task detail + comments         |
| PUT    | `/api/tasks/<id>`                | Update task                    |
| DELETE | `/api/tasks/<id>`                | Delete task + comments         |
| POST   | `/api/tasks/<id>/comments`       | Add comment                    |

**Query params for GET `/api/tasks`:**
```
?status=todo|in_progress|completed
?priority=low|medium|high
?project_id=<id>
?assignee=<user_id>
?search=<text>
```

### Kanban

| Method | Endpoint            | Description                     |
|--------|---------------------|---------------------------------|
| GET    | `/api/kanban`       | Board grouped by status         |
| POST   | `/api/kanban/move`  | Move card to new status         |

### Calendar

| Method | Endpoint            | Description                     |
|--------|---------------------|---------------------------------|
| GET    | `/api/calendar`     | Tasks & projects by month       |

**Query params:** `?month=2024-11`

### Users & Profile

| Method | Endpoint            | Description              |
|--------|---------------------|--------------------------|
| GET    | `/api/users`        | All users (no passwords) |
| GET    | `/api/profile`      | Current user profile     |
| PUT    | `/api/profile`      | Update profile           |

### Notifications & Activity

| Method | Endpoint                     | Description                 |
|--------|------------------------------|-----------------------------|
| GET    | `/api/notifications`         | User notifications          |
| POST   | `/api/notifications/read`    | Mark all as read            |
| GET    | `/api/activity`              | User activity log (last 50) |
| GET    | `/api/search?q=<query>`      | Global full-text search     |

---

## 🔌 Socket.IO Events

### Client → Server

| Event          | Payload                          | Description              |
|----------------|----------------------------------|--------------------------|
| `join_project` | `{ project_id }`                 | Subscribe to project room|
| `typing`       | `{ task_id }`                    | Emit typing indicator    |

### Server → Client

| Event            | Payload                          | Description              |
|------------------|----------------------------------|--------------------------|
| `connected`      | `{ status, user }`               | Connection confirmed     |
| `notification`   | `{ title, message, type }`       | Real-time alert          |
| `task_created`   | `{ task_id, title, status }`     | New task broadcast       |
| `task_updated`   | `{ task_id, update }`            | Task update broadcast    |
| `task_deleted`   | `{ task_id }`                    | Task removed             |
| `task_completed` | `{ task_id, title }`             | Completion event         |
| `kanban_move`    | `{ task_id, new_status }`        | Card moved on board      |
| `project_created`| `{ project_id, name }`           | New project              |
| `new_comment`    | `{ task_id, user_name, content }`| Live comment             |
| `user_typing`    | `{ user, task_id }`              | Typing indicator         |

---

## 🎨 UI Features

- **Dark / Light mode** — persisted in localStorage
- **Animated stat counters** — AOS scroll animations + JS count-up
- **Confetti burst** — fires on first task completion per session
- **Ripple effect** — on all button clicks
- **Keyboard shortcuts:**
  - `⌘K` / `Ctrl+K` — focus global search
  - `Escape` — close any modal
  - `⌘N` / `Ctrl+N` — open new task modal (on Tasks page)
- **Scroll-to-top button** — appears after 300px scroll
- **Skeleton loaders** — on data-fetching states
- **Auto-scroll** activity feed with live Socket.IO updates
- **Drag & drop** Kanban with touch support
- **Typing indicator** in task comments

---

## 🗄 MongoDB Collections

```
tasksphere
├── users           (name, email, password, role, avatar, bio, phone, department…)
├── projects        (name, description, status, priority, owner_id, members, deadline, color…)
├── tasks           (title, description, project_id, assignee_id, priority, status, deadline, tags…)
├── comments        (task_id, user_id, user_name, content, created_at)
├── notifications   (user_id, title, message, type, read, timestamp)
├── activity_logs   (user_id, action, entity_type, entity_id, description, timestamp)
└── files           (task_id, uploaded_by, filename, path, size, mimetype, uploaded_at)
```

---

## ⚙️ Environment Variables (optional `.env`)

```env
SECRET_KEY=your_secret_key_here
MONGO_URI=mongodb://localhost:27017/tasksphere
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_MB=16
PORT=5000
```

---

## 🐞 Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| MongoDB connection refused | Start MongoDB: `mongod` or `brew services start mongodb-community` |
| Socket.IO not connecting | Ensure `eventlet` is installed and `eventlet.monkey_patch()` is at top of `app.py` |
| `AttributeError: 'NoneType'` on session | Ensure `SECRET_KEY` is set in `app.config` |
| Port 5000 in use | Change port in `app.py`: `socketio.run(app, port=5001)` |

---

## 📄 License

MIT License — Free for personal and commercial use.

---

*Built with ❤️ using Flask + Socket.IO + MongoDB + Vanilla JS*