# Nexora Msg App

Nexora Msg App is a modular group-chat project with two clearly separated runtimes:

- `server` (FastAPI + MySQL + admin panel)
- `app` (Flask launcher + browser UI in JavaScript)

It is intentionally a **single shared server chat** (Discord-like baseline) without channels, DMs, voice, video, or reactions.

## Table of Contents

- [Project Goals](#project-goals)
- [Core Features](#core-features)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Security Notes](#security-notes)
- [Documentation Map](#documentation-map)

## Project Goals

- Keep implementation simple, readable, and modular.
- Keep `app` and `server` separated for easier learning and future upgrades.
- Provide practical admin tooling for user/chat/upload management.
- Support Docker-first backend setup with persistent DB and upload volumes.

## Core Features

- User login with JWT bearer auth.
- Login UI with three connection fields: protocol + domain/IP + port.
- Shared group chat with polling refresh.
- Reply-to-message (single-level, no threads).
- Message delete:
  - user deletes own messages,
  - admin can delete any message.
- Active users sidebar (online/offline indicator via presence heartbeat).
- Multi-file upload per message (text only, files only, or text + files).
- Upload limit:
  - persistent server setting,
  - shown to users,
  - validated in frontend and backend using total selected upload size.
- Upload controls in user UI:
  - remove single selected file before send,
  - progress indicator during upload.
- Upload availability states:
  - attachments can be marked unavailable,
  - UI shows `Attachment was removed by admin` / `File no longer available on server`.
- Admin panel tools:
  - create user,
  - change any user password,
  - delete user with full data cleanup,
  - delete messages,
  - change upload limit,
  - disable/enable uploads globally,
  - clear all uploads,
  - clear all messages and attachments.
- Admin auto logout after 2 minutes of inactivity.
- User app auth is session-only (does not survive closing browser tab/window).
- Docker persistence:
  - `mysql_data` for MySQL,
  - `chat_uploads` for uploaded files.

## Architecture at a Glance

- `app` serves HTML/CSS/JS locally and calls the remote `server` API.
- `server` owns authentication, authorization, persistence, upload storage, and admin GUI.
- `server` stores data in MySQL using SQLAlchemy models.
- Upload files are stored on disk in `UPLOADS_DIR` and mapped to Docker volume in containerized mode.

## Project Structure

```text
NexoraMsgApp/
|-- README.md
|-- app/
|   |-- main.py
|   |-- config.py
|   |-- gui.py
|   |-- routes.py
|   |-- requirements.txt
|   |-- templates/
|   |   `-- index.html
|   `-- static/
|       |-- app.js
|       `-- style.css
|-- server/
|   |-- main.py
|   |-- config.py
|   |-- database.py
|   |-- models.py
|   |-- schemas.py
|   |-- auth.py
|   |-- routes.py
|   |-- admin.py
|   |-- presence.py
|   |-- chat_settings.py
|   |-- upload_service.py
|   |-- user_cleanup.py
|   |-- requirements.txt
|   |-- Dockerfile
|   |-- docker-compose.yml
|   |-- .env.example
|   |-- initdb/
|   |   `-- 01-init.sql
|   |-- templates/
|   |   |-- admin_login.html
|   |   `-- admin_dashboard.html
|   |-- static/
|   |   `-- admin.css
|   `-- uploads/
|       `-- .gitkeep
`-- README/
    |-- README.md
    |-- project_overview.md
    |-- architecture.md
    |-- features.md
    |-- server_explained.md
    |-- app_explained.md
    |-- database_explained.md
    |-- api_reference.md
    |-- admin_panel_explained.md
    |-- setup_guide.md
    |-- usage_guide.md
    |-- program_flow_step_by_step.md
    |-- file_by_file_explanation.md
    `-- technology_decisions.md
```

## Quick Start

### 1) Start server (Docker)

```bash
cd server
cp .env.example .env
docker compose up --build
```

Server endpoints:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/api/health`
- Admin login: `http://localhost:8000/admin/login`

### 2) Start app

```bash
cd app
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Local app URL:

- `http://127.0.0.1:5000`

## Configuration

Server config comes from `server/.env`.

Important keys:

- `DATABASE_URL`
- `SECRET_KEY`
- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`
- `UPLOADS_DIR`
- `DEFAULT_MAX_UPLOAD_MB`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

Docker volumes in `server/docker-compose.yml`:

- `mysql_data` (database)
- `chat_uploads` (uploaded files)

## Security Notes

- Passwords are hashed with bcrypt (`passlib`).
- Protected API endpoints require bearer token.
- Admin panel uses server-side session.
- Admin panel auto-logout after inactivity (2 minutes).
- User app auth state is kept in `sessionStorage` and not restored after closing tab/window.
- Backend validates upload limits and upload-enabled state (not frontend-only).

## Documentation Map

Detailed docs are in [`README/README.md`](README/README.md).

Recommended order:

1. `README/project_overview.md`
2. `README/architecture.md`
3. `README/features.md`
4. `README/setup_guide.md`
5. `README/server_explained.md`
6. `README/app_explained.md`
7. `README/api_reference.md`
8. `README/admin_panel_explained.md`
9. `README/program_flow_step_by_step.md`
10. `README/file_by_file_explanation.md`

