# Server Explained

## 1) Server role

`server` is the central authority for:

- authentication and authorization,
- message and attachment persistence,
- upload policy enforcement,
- admin panel operations,
- runtime settings (upload limit, uploads enabled).

## 2) Startup lifecycle (`server/main.py`)

On startup:

1. `init_db()` creates tables and applies lightweight compatibility column checks.
2. `ensure_uploads_dir()` prepares upload folder.
3. `create_default_admin()` ensures admin exists.
4. Upload settings are initialized in `app_settings` if missing.
5. Middleware is attached:
   - `SessionMiddleware` for admin panel,
   - `CORSMiddleware` for browser API calls.
6. API router and admin router are mounted.

## 3) Main modules

- `config.py`: env-backed settings.
- `database.py`: SQLAlchemy engine/session/base and startup schema compatibility checks.
- `models.py`: `User`, `Message`, `MessageAttachment`, `AppSetting`.
- `schemas.py`: API request/response models.
- `auth.py`: bcrypt hashing + JWT auth dependencies.
- `presence.py`: online status heartbeat.
- `chat_settings.py`: persistent upload limit + upload enabled setting logic.
- `upload_service.py`: secure filename handling, storage, size validation, cleanup.
- `user_cleanup.py`: user cascade cleanup logic (DB + file cleanup safety).
- `routes.py`: `/api` endpoints.
- `admin.py`: server-rendered admin panel routes.

## 4) API auth behavior

- Login endpoint validates username/password hash.
- JWT is issued with `sub` and `is_admin` fields.
- Protected endpoints require bearer token.
- `get_current_admin` enforces admin role for admin API endpoints.

## 5) Chat behavior

- Messages are loaded with author and reply context.
- Reply stores parent id + fallback snapshot (`reply_to_username`, `reply_to_content`).
- Deleting parent message does not break child replies.
- Message deletion also cleans related files when needed.

## 6) Upload behavior

- `POST /api/messages` accepts multipart with `files` list.
- Backend enforces total upload size for all files in request.
- Uploads are saved with generated storage key.
- Attachment metadata stored in `message_attachments`.
- Legacy single-file fields on `messages` are kept for compatibility.

## 7) Upload policy behavior

- Upload size limit is stored in `app_settings` (`max_upload_bytes`).
- Upload enabled/disabled is stored in `app_settings` (`uploads_enabled`).
- Endpoint `/api/settings/upload-limit` returns both values for frontend sync.
- If uploads are disabled, backend rejects upload attempts with clear 403 message.

## 8) Admin panel behavior

Admin panel routes are in `admin.py`:

- session-based login/logout,
- dashboard rendering,
- user create/delete,
- password change,
- message delete,
- upload limit update,
- clear all messages,
- clear all uploads,
- uploads enable/disable.

Additional safeguards:

- self-delete protection for current admin,
- confirmation dialogs in UI for dangerous actions,
- inactivity auto-logout handling (frontend timer + logout route).

## 9) Presence behavior

- Presence is in-memory and time-based.
- Each authenticated request marks user active.
- Timeout removes stale active users.
- `/api/users/presence` returns full user list with online boolean.

## 10) What to update when extending server

If you add backend features, update all of these together:

- model(s),
- schema(s),
- route handlers,
- admin panel UI if needed,
- documentation (`README/api_reference.md`, `README/features.md`).
