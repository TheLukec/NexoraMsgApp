# File by File Explanation

This document explains each important file using the same structure:

- What it does.
- Why it exists.
- How it works with other files.
- Main functions/classes/code blocks.
- What to watch when changing it.

## Root files

### `.gitignore`

- What it does: prevents virtualenv, cache, and secret env files from being committed.
- Why it exists: keeps repository clean and avoids leaking credentials.
- Collaboration: affects git behavior for both `app` and `server`.
- Main parts: ignore rules for `.venv`, `__pycache__`, `*.pyc`, `.env`.
- Change caution: do not remove `.env` ignores unless you intentionally version config secrets.

### `README.md`

- What it does: gives top-level project description and quick run instructions.
- Why it exists: first entry point for new users of the repository.
- Collaboration: references both runtime components and Docker setup.
- Main parts: architecture summary, setup commands, endpoint list.
- Change caution: keep commands synchronized with actual file names and ports.

## App files

### `app/config.py`

- What it does: stores local app host/port and browser auto-open flag.
- Why it exists: central config avoids hardcoded values in startup logic.
- Collaboration: imported by `app/main.py`.
- Main parts: `Settings` dataclass and `settings` instance.
- Change caution: if you rename config variables, update startup references in `main.py`.

### `app/gui.py`

- What it does: opens system browser after short delay.
- Why it exists: improves user experience by launching UI automatically.
- Collaboration: called from `app/main.py` startup block.
- Main parts: `open_in_browser(url)` and timer callback.
- Change caution: too short delay can open browser before Flask is ready.

### `app/main.py`

- What it does: creates Flask app, registers routes, starts web server.
- Why it exists: runtime entry point for local client app.
- Collaboration: imports `config.py`, `gui.py`, `routes.py`.
- Main parts: `create_app()`, global `app`, `if __name__ == "__main__"` block.
- Change caution: keep static/template paths valid when reorganizing folders.

### `app/routes.py`

- What it does: defines HTTP route for root page.
- Why it exists: separates route declarations from startup file.
- Collaboration: blueprint registered in `app/main.py`.
- Main parts: blueprint `web`, route `index()`.
- Change caution: if route path changes, update user instructions.

### `app/requirements.txt`

- What it does: lists Python dependency for local app runtime.
- Why it exists: reproducible setup for client app environment.
- Collaboration: used in setup guide commands.
- Main parts: `Flask` package requirement.
- Change caution: keep compatible with Python 3.12.10.

### `app/templates/index.html`

- What it does: renders login UI and chat UI containers.
- Why it exists: structure for browser interface served by Flask.
- Collaboration: styled by `styles.css`, controlled by `app.js`.
- Main parts: login form, chat panel, message list container, send form.
- Change caution: keep element IDs in sync with JavaScript selectors.

### `app/static/app.js`

- What it does: frontend logic for login, token storage, chat refresh, message send.
- Why it exists: browser-side controller for user interaction.
- Collaboration: calls server API endpoints and updates HTML from `index.html`.
- Main parts: state object, `login()`, `fetchMessages()`, `sendMessage()`, `logout()`.
- Change caution: auth header handling must stay consistent on all protected requests.

### `app/static/styles.css`

- What it does: styles login and chat screens.
- Why it exists: keeps UI readable and usable on desktop/mobile.
- Collaboration: linked by `index.html`.
- Main parts: layout, message list styling, responsive media query.
- Change caution: avoid removing `.hidden` behavior used by JS view switching.

## Server files

### `server/config.py`

- What it does: loads environment-driven server settings.
- Why it exists: centralized configuration for secrets, DB URL, host, CORS.
- Collaboration: imported by `main.py`, `database.py`, and `auth.py`.
- Main parts: `Settings` dataclass, `parsed_cors_origins()`.
- Change caution: if settings keys change, update `.env.example` and docs.

### `server/database.py`

- What it does: defines SQLAlchemy engine/session/base and DB init helper.
- Why it exists: shared DB access layer for all routes.
- Collaboration: used by `models.py`, `main.py`, `routes.py`, `admin.py`.
- Main parts: `engine`, `SessionLocal`, `Base`, `get_db()`, `init_db()`.
- Change caution: keep `get_db()` lifecycle pattern to avoid connection leaks.

### `server/models.py`

- What it does: declares ORM models for users and messages.
- Why it exists: defines relational database schema in code.
- Collaboration: queried by API and admin routes.
- Main parts: classes `User`, `Message` and relationships.
- Change caution: schema changes require route/schema/doc updates and migration strategy.

### `server/schemas.py`

- What it does: defines API request/response models.
- Why it exists: validates input and standardizes output payloads.
- Collaboration: imported by `routes.py`.
- Main parts: `LoginRequest`, `UserCreate`, `UserPublic`, `MessageCreate`, `MessageOut`, `StatsOut`.
- Change caution: response model edits can break frontend expectations.

### `server/auth.py`

- What it does: handles password hashing and JWT authentication dependencies.
- Why it exists: keeps security logic isolated and reusable.
- Collaboration: used by `routes.py`, `admin.py`, and `main.py`.
- Main parts: `hash_password`, `verify_password`, `create_access_token`, `get_current_user`, `get_current_admin`.
- Change caution: secret key and algorithm changes invalidate old tokens.

### `server/routes.py`

- What it does: exposes REST API endpoints for chat and user management.
- Why it exists: core server business logic lives here.
- Collaboration: uses DB sessions, models, schemas, and auth dependencies.
- Main parts: login endpoint, message read/write endpoints, admin user endpoints, stats endpoint.
- Change caution: never remove auth dependencies from protected endpoints.

### `server/admin.py`

- What it does: provides admin web GUI routes with session auth.
- Why it exists: owner-friendly management interface without API tooling.
- Collaboration: uses Jinja templates, DB models, password verification/hash functions.
- Main parts: login/logout, dashboard render, create/delete user routes.
- Change caution: keep `_load_admin_user` checks in place to protect admin routes.

### `server/main.py`

- What it does: application assembly and startup lifecycle.
- Why it exists: bootstraps entire server runtime.
- Collaboration: wires config, middleware, routers, static files, DB init.
- Main parts: `create_default_admin`, lifespan startup, `app` object, root endpoint.
- Change caution: avoid breaking startup order (`init_db` before API use).

### `server/requirements.txt`

- What it does: lists backend dependencies.
- Why it exists: reproducible backend environment setup.
- Collaboration: used by Docker image build and local setup.
- Main parts: FastAPI, SQLAlchemy, MySQL driver, auth/crypto libs.
- Change caution: update versions carefully to avoid compatibility breaks.

### `server/Dockerfile`

- What it does: defines container image for backend server.
- Why it exists: consistent deployment runtime across machines.
- Collaboration: built by `docker-compose.yml`.
- Main parts: python base image, dependency install, code copy, uvicorn command.
- Change caution: if command changes, keep port and compose mapping synchronized.

### `server/docker-compose.yml`

- What it does: orchestrates MySQL and server containers.
- Why it exists: one-command startup for complete backend stack.
- Collaboration: uses `.env` values and `Dockerfile`.
- Main parts: `mysql` service, `server` service, healthcheck, volume.
- Change caution: DB credentials must match `DATABASE_URL`.

### `server/.env.example`

- What it does: template for runtime environment variables.
- Why it exists: documents required configuration keys.
- Collaboration: copied to `.env` and consumed by compose/server.
- Main parts: DB credentials, app host/port, secret key, default admin values.
- Change caution: do not store real production secrets in this template.

### `server/initdb/01-init.sql`

- What it does: sets character handling during initial MySQL init.
- Why it exists: ensures expected text encoding baseline.
- Collaboration: executed automatically by MySQL container init hook.
- Main parts: `SET NAMES utf8mb4`.
- Change caution: keep init scripts idempotent and safe on first startup.

### `server/templates/admin_login.html`

- What it does: admin login page template.
- Why it exists: entry point for admin panel authentication.
- Collaboration: rendered by `admin.py`, styled by `static/admin.css`.
- Main parts: username/password form and error notice block.
- Change caution: form field names must match backend `Form(...)` parameter names.

### `server/templates/admin_dashboard.html`

- What it does: dashboard template with stats, create form, users table.
- Why it exists: central admin UI for user management.
- Collaboration: rendered by `admin.py`.
- Main parts: overview stats section, create-user form, delete buttons.
- Change caution: action URLs must match admin route paths.

### `server/static/admin.css`

- What it does: styles admin login and dashboard pages.
- Why it exists: improves readability and usability of admin panel.
- Collaboration: loaded by both admin templates.
- Main parts: layout styles, table formatting, buttons, notice states.
- Change caution: do not remove classes used in templates (`notice`, `danger`, etc.).

## README folder files

### `README/README.md`

- What it does: index for the detailed documentation set.
- Why it exists: helps reader navigate documents quickly.
- Collaboration: links conceptual and practical guides.
- Main parts: document list and recommended reading order.
- Change caution: keep links and file names aligned with actual docs.

### `README/project_overview.md`

- What it does: explains goals, architecture, and constraints.
- Why it exists: high-level context for presentations and onboarding.
- Collaboration: complements technical deep-dive docs.
- Main parts: architecture map, design goals, future upgrade ideas.
- Change caution: keep overview synchronized with real implementation.

### `README/app_explained.md`

- What it does: deep explanation of client app behavior.
- Why it exists: clarifies browser and Flask responsibilities.
- Collaboration: pairs with `server_explained.md` and flow guide.
- Main parts: startup sequence, frontend state, API interaction.
- Change caution: update when app-side auth or state logic changes.

### `README/server_explained.md`

- What it does: deep explanation of backend architecture and APIs.
- Why it exists: makes backend design easy to explain to others.
- Collaboration: references auth, DB, and admin docs.
- Main parts: startup flow, endpoint groups, module roles.
- Change caution: update if routes/middleware/auth model changes.

### `README/database_explained.md`

- What it does: explains schema and data lifecycle.
- Why it exists: provides clear model-level understanding.
- Collaboration: supports server and admin documentation.
- Main parts: tables, relations, migration notes.
- Change caution: update immediately after schema changes.

### `README/admin_panel_explained.md`

- What it does: explains admin GUI architecture and security behavior.
- Why it exists: admin features are separate from API auth model.
- Collaboration: tied to `server/admin.py` and admin templates.
- Main parts: route descriptions, session flow, dashboard logic.
- Change caution: keep route descriptions aligned with implementation.

### `README/setup_guide.md`

- What it does: installation and startup instructions.
- Why it exists: step-by-step reproducibility for new users.
- Collaboration: uses `requirements.txt`, `.env.example`, docker files.
- Main parts: Docker path, non-Docker path, config explanation.
- Change caution: command updates must match current runtime.

### `README/usage_guide.md`

- What it does: practical operational instructions for admin/users.
- Why it exists: clarifies day-to-day usage and troubleshooting.
- Collaboration: depends on setup + admin panel + app behavior docs.
- Main parts: owner workflow, user workflow, troubleshooting section.
- Change caution: keep with latest UI/API behavior.

### `README/program_flow_step_by_step.md`

- What it does: explains runtime flow in sequential scenarios.
- Why it exists: ideal for teaching and presenting execution logic.
- Collaboration: bridges conceptual docs and source code.
- Main parts: server start, app start, login, send message, admin actions.
- Change caution: update when control flow changes in main/auth/routes/admin code.
