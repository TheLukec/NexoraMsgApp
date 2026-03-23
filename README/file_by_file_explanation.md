# File by File Explanation

This document explains the most important project files.
For each file: what it does, why it exists, interactions, main parts, and change cautions.

## Root

## `README.md`

- What: project landing documentation.
- Why: first overview for setup and architecture.
- Interacts with: references all files in `README/`.
- Main parts: features, quick start, structure, links.
- Change caution: keep commands and structure synchronized with real files.

## App (`app/`)

## `app/main.py`

- What: Flask entry point.
- Why: serves browser UI locally.
- Interacts with: `config.py`, `gui.py`, `routes.py`.
- Main parts: `create_app()`, startup block.
- Change caution: keep static/template paths aligned with filesystem.

## `app/config.py`

- What: local app host/port/browser settings.
- Why: avoid hardcoded constants in runtime code.
- Interacts with: `app/main.py`.
- Main parts: `Settings` dataclass.
- Change caution: update docs when defaults change.

## `app/gui.py`

- What: delayed browser opener.
- Why: opens app page automatically after startup.
- Interacts with: called by `app/main.py`.
- Main parts: `open_in_browser`.
- Change caution: avoid too-short delay that races Flask startup.

## `app/routes.py`

- What: Flask route declarations.
- Why: keep route logic separated from bootstrapping.
- Interacts with: blueprint registration in `app/main.py`.
- Main parts: `/` route rendering `index.html`.
- Change caution: if route path changes, update docs and launcher expectations.

## `app/templates/index.html`

- What: main UI markup.
- Why: defines login + chat + sidebar structure.
- Interacts with: IDs/classes used by `app.js` and `style.css`.
- Main parts: login form, chat panel, reply preview, upload controls, sidebar sections.
- Change caution: keep element IDs stable or update JS selectors.

## `app/static/app.js`

- What: primary frontend controller.
- Why: owns runtime UI state and API communication.
- Interacts with: all `/api` endpoints and DOM in `index.html`.
- Main parts:
  - auth/login/logout,
  - session restore (sessionStorage),
  - message polling and rendering,
  - reply state,
  - delete message,
  - presence polling,
  - upload selection/progress/validation,
  - upload-limit refresh and uploads-enabled handling.
- Change caution:
  - keep auth handling consistent for all protected calls,
  - avoid duplicating submit logic,
  - preserve scroll behavior and status feedback.

## `app/static/style.css`

- What: app UI styling.
- Why: keeps layout usable and readable on desktop/mobile.
- Interacts with: class names in `index.html` + generated elements from `app.js`.
- Main parts: login layout, chat bubbles, sidebar, upload row, progress bar, wrapping fixes.
- Change caution: do not break `hidden` and flex alignment classes used in JS flow.

## Server (`server/`)

## `server/main.py`

- What: FastAPI app assembly and startup lifecycle.
- Why: central boot process.
- Interacts with: `database.py`, `chat_settings.py`, `upload_service.py`, routers.
- Main parts: lifespan startup, middleware setup, router include.
- Change caution: startup order matters (DB and settings before traffic).

## `server/config.py`

- What: environment-backed server settings.
- Why: centralizes runtime config.
- Interacts with: most backend modules.
- Main parts: DB URL, secrets, upload config, defaults.
- Change caution: if key names change, update `.env.example`, compose, and docs.

## `server/database.py`

- What: SQLAlchemy engine/session/base + startup compatibility checks.
- Why: shared DB plumbing and backwards-safe column initialization.
- Interacts with: models, routes, startup.
- Main parts: `get_db()`, `init_db()`, compatibility helpers.
- Change caution: DB compatibility logic must remain idempotent.

## `server/models.py`

- What: ORM schema.
- Why: source of truth for DB structure.
- Interacts with: all route/business modules.
- Main parts: `User`, `Message`, `MessageAttachment`, `AppSetting`.
- Change caution: schema changes require synchronized updates in schemas/routes/docs.

## `server/schemas.py`

- What: request/response models.
- Why: input validation and stable API payloads.
- Interacts with: `routes.py`.
- Main parts: login/user/message/attachment/settings response models.
- Change caution: changing response shape may break frontend rendering.

## `server/auth.py`

- What: password hashing and JWT auth dependencies.
- Why: isolate auth logic from route handlers.
- Interacts with: routes and admin helper logic.
- Main parts: `hash_password`, `verify_password`, token creation, dependency guards.
- Change caution: changing token claims requires frontend/backward compatibility checks.

## `server/presence.py`

- What: in-memory online tracking.
- Why: lightweight online/offline state.
- Interacts with: `routes.py` heartbeat calls.
- Main parts: `mark_active`, `mark_inactive`, timeout cleanup.
- Change caution: this is process-memory only, not cross-instance persistent.

## `server/chat_settings.py`

- What: persistent server settings service.
- Why: runtime-configurable upload policy.
- Interacts with: `routes.py`, `admin.py`, startup bootstrap.
- Main parts: get/set for `max_upload_bytes` and `uploads_enabled`.
- Change caution: validate ranges and normalize boolean values.

## `server/upload_service.py`

- What: upload file handling.
- Why: secure file naming/storage/size validation.
- Interacts with: `routes.py`, cleanup routines.
- Main parts: sanitize name, generate storage key, save files, delete files.
- Change caution:
  - never trust user filename/path,
  - keep traversal protections,
  - preserve total-size validation.

## `server/user_cleanup.py`

- What: deep cleanup when deleting user data.
- Why: prevent orphan DB rows/files.
- Interacts with: `routes.py` and `admin.py` delete-user actions.
- Main parts: collect message IDs, cleanup attachments/files, preserve reply integrity.
- Change caution: keep delete order predictable and safe against shared file references.

## `server/routes.py`

- What: REST API logic for app clients.
- Why: main business operations.
- Interacts with: auth, models, schemas, settings, upload service, presence.
- Main parts:
  - auth endpoints,
  - message CRUD,
  - reply support,
  - attachment downloads,
  - upload-limit endpoint,
  - presence,
  - admin API user management.
- Change caution: authorization checks must stay strict.

## `server/admin.py`

- What: admin panel routes and operations.
- Why: browser GUI for operational management.
- Interacts with: templates, chat settings, cleanup utilities.
- Main parts:
  - session login/logout,
  - dashboard render,
  - user/message actions,
  - maintenance actions,
  - upload toggle/limit,
  - inactivity logout notice handling.
- Change caution: always enforce `_load_admin_user` on protected routes.

## `server/templates/admin_login.html`

- What: admin login UI.
- Why: entry point for admin session auth.
- Interacts with: `admin.py` notices/errors.
- Main parts: login form and notice rendering.
- Change caution: keep input names aligned with backend `Form(...)` fields.

## `server/templates/admin_dashboard.html`

- What: admin dashboard UI.
- Why: manage users, messages, uploads, and settings.
- Interacts with: `admin.py` forms and notices.
- Main parts:
  - stats,
  - create/change/delete forms,
  - danger zone actions,
  - scroll-preserve script,
  - inactivity auto-logout timer script.
- Change caution: action URLs and hidden input names must match route handlers.

## `server/static/admin.css`

- What: admin panel styling.
- Why: readable and usable operations UI.
- Interacts with: both admin templates.
- Main parts: panel/table/button/danger-zone styles.
- Change caution: keep class names synchronized with templates.

## `server/docker-compose.yml`

- What: container orchestration for server + MySQL.
- Why: reproducible setup with persistent storage.
- Interacts with: Dockerfile, `.env`, `initdb`, volumes.
- Main parts: `mysql`, `server`, `mysql_data`, `chat_uploads`.
- Change caution: keep `UPLOADS_DIR` and volume mount path aligned.

## `server/Dockerfile`

- What: image definition for server container.
- Why: deterministic backend runtime.
- Interacts with: `requirements.txt`, source files, compose.
- Main parts: Python 3.12.10 base, install deps, uvicorn command.
- Change caution: keep exposed port/command consistent with compose.

## `server/.env.example`

- What: environment template.
- Why: documents required runtime variables.
- Interacts with: config + compose.
- Main parts: DB, auth, admin defaults, uploads.
- Change caution: template only; do not put real secrets in VCS.

## `server/initdb/01-init.sql`

- What: MySQL init script.
- Why: ensures expected charset defaults on fresh DB init.
- Interacts with: MySQL container startup.
- Main parts: `SET NAMES utf8mb4`.
- Change caution: keep startup scripts safe and idempotent.

## Documentation files (`README/`)

- These files explain architecture, setup, usage, API, and module responsibilities.
- Change caution: whenever features change, update docs in the same PR/commit.

