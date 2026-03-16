# Nexora v6.7 - Simple Group Chat

Simple modular project with two clearly separated parts:

- `server`: central group chat server (FastAPI + MySQL + admin panel)
- `app`: local user client app (Flask + browser UI + JavaScript)

The system is a lightweight Discord-like server alternative for one shared group chat (no DMs).

## Python Version

Both `server` and `app` are designed for **Python 3.12.10**.

## Project Structure

```text
Nexora_v6.7/
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
|       `-- styles.css
`-- server/
    |-- main.py
    |-- config.py
    |-- database.py
    |-- models.py
    |-- schemas.py
    |-- auth.py
    |-- routes.py
    |-- admin.py
    |-- requirements.txt
    |-- Dockerfile
    |-- docker-compose.yml
    |-- .env.example
    |-- initdb/
    |   `-- 01-init.sql
    |-- templates/
    |   |-- admin_login.html
    |   `-- admin_dashboard.html
    `-- static/
        `-- admin.css
```

## How It Works

1. Host/admin starts `server` (with Docker recommended).
2. Server connects to MySQL and stores users + messages.
3. User starts `app` locally on their computer.
4. Browser opens local app UI and asks for:
   - server URL/IP
   - username
   - password
5. After login, user enters shared group chat and can send/read messages.

## Server Setup (Docker Recommended)

1. Open terminal in `server`:
   ```bash
   cd server
   ```
2. Create `.env` from example:
   ```bash
   cp .env.example .env
   ```
   On Windows PowerShell:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Start services:
   ```bash
   docker compose up --build
   ```
4. Access:
   - API root: `http://localhost:8000/`
   - Admin panel: `http://localhost:8000/admin/login`

Default admin credentials come from `.env`:
- `DEFAULT_ADMIN_USERNAME=admin`
- `DEFAULT_ADMIN_PASSWORD=admin123`

Change these before production use.

## Server Setup (Without Docker)

1. In `server` folder:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Windows PowerShell activation:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. Ensure MySQL is running and update `DATABASE_URL` in environment.
3. Run:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## App Setup

1. Open terminal in `app`:
   ```bash
   cd app
   ```
2. Create virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Windows PowerShell activation:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Start app:
   ```bash
   python main.py
   ```
4. Browser opens automatically on `http://127.0.0.1:5000`.

## Basic API Endpoints

- `POST /api/auth/login` - user login
- `GET /api/messages` - get chat messages
- `POST /api/messages` - send new message
- `GET /api/users` - list users (admin only)
- `POST /api/users` - create user (admin only)
- `DELETE /api/users/{user_id}` - delete user (admin only)

## Notes

- Passwords are hashed with bcrypt (`passlib`).
- No DMs, no voice/video, no files, no reactions.
- Code is intentionally simple and modular for easy upgrades.
