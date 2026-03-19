# Nexora Msg App - Simple Group Chat

Simple modular project with two clearly separated parts:

- `server`: central group chat server (FastAPI + MySQL + admin panel)
- `app`: local user client app (Flask + browser UI + JavaScript)

The system is a lightweight Discord-like server alternative for one shared group chat (no DMs).

## Python Version

Both `server` and `app` are designed for **Python 3.12.10**.

## Project Structure

```text
NexoraMsgApp/
|-- .gitattributes
|-- LICENSE
|-- README.md
|-- README/
|   |-- README.md
|   |-- project_overview.md
|   |-- app_explained.md
|   |-- server_explained.md
|   |-- database_explained.md
|   |-- admin_panel_explained.md
|   |-- technology_decisions.md
|   |-- file_by_file_explanation.md
|   |-- setup_guide.md
|   |-- usage_guide.md
|   `-- program_flow_step_by_step.md
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
    |-- .env
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
2. Start services:
   ```bash
   docker compose up --build
   ```
3. Access:
   - API root: `http://localhost:8000/`
   - Admin panel: `http://localhost:8000/admin/login`

## Docker Volumes (Persistent Data)

- MySQL data is stored in volume `mysql_data`.
- Uploaded chat files are stored in dedicated volume `chat_uploads` (mounted to `/app/uploads` in server container).
- Server upload path is configured via environment variable `UPLOADS_DIR` (Docker compose sets it to `/app/uploads`).

Check volumes:

```bash
docker volume ls
```

Inspect uploads volume:

```bash
docker volume inspect chat_uploads
```

Backup uploaded files:

```bash
docker run --rm -v chat_uploads:/volume -v ${PWD}:/backup alpine sh -c "cd /volume && tar czf /backup/chat_uploads_backup.tar.gz ."
```

Restore uploaded files:

```bash
docker run --rm -v chat_uploads:/volume -v ${PWD}:/backup alpine sh -c "cd /volume && tar xzf /backup/chat_uploads_backup.tar.gz"
```

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

## Detailed Documentation

For full in-depth project documentation, open the `README/` folder.
Start with `README/README.md` and then continue through the detailed guides.
