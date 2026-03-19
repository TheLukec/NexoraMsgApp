# Setup Guide

## Prerequisites

- Python 3.12.10
- Docker Desktop (recommended for server + MySQL)
- Optional: local MySQL if you skip Docker

## Quick start (recommended path)

### 1) Start server with Docker

Run from project root:

```bash
cd server
cp .env.example .env
docker compose up --build
```

Windows PowerShell:

```powershell
cd server
Copy-Item .env.example .env
docker compose up --build
```

### 2) Start local app

Open second terminal from project root:

```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3) Open browser

The app opens automatically at:
`http://127.0.0.1:5000`

## `.env` configuration explained (server)

Copy `server/.env.example` to `server/.env`.

Important variables:

- `DATABASE_URL`: SQLAlchemy connection URL.
- `SECRET_KEY`: session + JWT signing secret.
- `DEFAULT_ADMIN_USERNAME`: initial admin name.
- `DEFAULT_ADMIN_PASSWORD`: initial admin password.
- `CORS_ALLOW_ORIGINS`: allowed browser origins (`*` for development).
- `UPLOADS_DIR`: upload storage path (in Docker compose it is set to `/app/uploads`).
- `DEFAULT_MAX_UPLOAD_MB`: default upload size limit in MB.

MySQL container variables:

- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

## Admin account creation logic

Admin account is created automatically at server startup only if missing.
Values come from:

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

If admin already exists, startup will not overwrite it.

## Running server without Docker

1. Ensure MySQL instance exists and database is created.
2. Set environment values manually (especially `DATABASE_URL`).
3. Install dependencies:

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```


## Docker persistence for uploads

`server/docker-compose.yml` defines two persistent volumes:

- `mysql_data` for MySQL data
- `chat_uploads` for uploaded files

The server container mounts `chat_uploads` to `/app/uploads` and compose sets `UPLOADS_DIR=/app/uploads`.

Check volume existence:

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

## Basic verification checks

- `http://localhost:8000/api/health` returns status.
- `http://localhost:8000/admin/login` opens admin login page.
- local app page loads and login form is visible.
