# Server Explained

## Purpose of `server`

The `server` folder is the central backend of the project.
It exposes API endpoints for authentication, messages, and user management.
It also serves the admin panel UI.

## Framework choice

FastAPI was selected because:

- clean request/response modeling with Pydantic.
- simple dependency injection for auth/db.
- straightforward async-ready architecture.
- good fit for modular API structure.

## Startup flow

Entry point is `server/main.py`.

When server starts:

1. `init_db()` creates tables if missing.
2. `create_default_admin()` ensures initial admin account exists.
3. middleware is attached (sessions + CORS).
4. static files are mounted (`/static`).
5. API and admin routers are included.

## Module breakdown

`config.py`
- Central place for env-driven settings.
- Includes database URL, secrets, CORS, default admin credentials.

`database.py`
- SQLAlchemy engine/session setup.
- `get_db()` dependency for request-scoped sessions.

`models.py`
- ORM entities: `User`, `Message`.

`schemas.py`
- Pydantic request/response models.

`auth.py`
- Password hashing and verification.
- JWT create/decode logic.
- dependencies `get_current_user` and `get_current_admin`.

`routes.py`
- API endpoints under `/api`.
- login, chat, user management, stats.

`admin.py`
- Admin web routes (`/admin/...`).
- session-based admin login.
- dashboard + create/delete users.

## API endpoint groups

Public:
- `GET /api/health`
- `POST /api/auth/login`

Authenticated user:
- `GET /api/me`
- `GET /api/messages`
- `POST /api/messages`

Authenticated admin:
- `GET /api/users`
- `POST /api/users`
- `DELETE /api/users/{id}`
- `GET /api/stats`

## Auth model

Login receives username/password.
Server verifies password hash.
Server returns JWT token.
Token payload includes `sub` (username) and admin flag.
Protected routes require token and resolve current user via dependency.

## Admin panel model

Admin panel is classic server-rendered web:

- login form posts to `/admin/login`.
- server stores admin id in session cookie.
- dashboard validates session on every request.

This is separate from bearer-token API auth.

## What to watch when modifying `server`

- Keep clear separation between API auth and admin session auth.
- Do not bypass `get_current_admin` checks on admin APIs.
- Keep DB session lifecycle via `get_db`.
- If changing schemas, update ORM and docs together.
- If moving to production, rotate secrets and tighten CORS.
