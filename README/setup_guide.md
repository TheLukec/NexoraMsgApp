# Setup Guide

## 1) Requirements

- Python 3.12.10
- Docker Desktop (recommended for server stack)
- Modern browser

Optional:

- local MySQL if not using Docker

## 2) Server setup (recommended: Docker)

From project root:

```bash
cd server
cp .env.example .env
docker compose up --build
```

PowerShell alternative:

```powershell
cd server
Copy-Item .env.example .env
docker compose up --build
```

Server should be reachable at:

- `http://localhost:8000/`
- `http://localhost:8000/api/health`
- `http://localhost:8000/admin/login`

## 3) Docker persistence

Compose defines two persistent volumes:

- `mysql_data` for MySQL files,
- `chat_uploads` for uploaded attachments.

Check volumes:

```bash
docker volume ls
```

Inspect uploads volume:

```bash
docker volume inspect chat_uploads
```

Backup uploads:

```bash
docker run --rm -v chat_uploads:/volume -v ${PWD}:/backup alpine sh -c "cd /volume && tar czf /backup/chat_uploads_backup.tar.gz ."
```

Restore uploads:

```bash
docker run --rm -v chat_uploads:/volume -v ${PWD}:/backup alpine sh -c "cd /volume && tar xzf /backup/chat_uploads_backup.tar.gz"
```

## 4) Server `.env` configuration

Use `server/.env.example` as baseline.

Important keys:

- `DATABASE_URL`
- `SECRET_KEY`
- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `UPLOADS_DIR`
- `DEFAULT_MAX_UPLOAD_MB`
- `CORS_ALLOW_ORIGINS`

MySQL-related keys:

- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

## 5) App setup

From project root:

```bash
cd app
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The app starts on `http://127.0.0.1:5000` by default and opens browser automatically.

## 6) Optional local server setup (without Docker)

```bash
cd server
python -m venv .venv
# activate venv
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

You must provide a reachable MySQL and correct `DATABASE_URL`.

## 7) First-time login checks

1. Open admin panel and login with default admin credentials from `.env`.
2. Create at least one non-admin user.
3. Start app, connect to server, and login as that user.
4. Send a test message and optional file upload.

## 8) Common startup issues

- `Invalid or expired token`: user must login again.
- Upload rejected: check admin upload limit and uploads-enabled toggle.
- App reconnect problems: verify protocol/domain/port values.
- DB errors: check `docker compose ps` and `DATABASE_URL` consistency.
