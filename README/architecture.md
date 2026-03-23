# Architecture

## 1) Component separation

### `app` (client launcher)

- Flask serves static UI (`index.html`, `app.js`, `style.css`).
- Browser UI handles login input, chat interaction, rendering, and polling.
- Browser talks directly to server API via HTTP.

### `server` (shared backend)

- FastAPI exposes authenticated API endpoints (`/api/...`).
- Admin panel uses server-rendered templates (`/admin/...`).
- SQLAlchemy persists business data in MySQL.
- Upload service stores files to configured `UPLOADS_DIR`.

## 2) Communication flow

1. User starts `app` locally.
2. Browser opens local UI.
3. User enters server connection + credentials.
4. Browser sends `POST /api/auth/login` to server.
5. Server returns JWT token.
6. Browser stores token in `sessionStorage`.
7. Browser calls protected API endpoints with `Authorization: Bearer ...`.

## 3) Authentication model

### API auth (user app)

- JWT bearer token from `/api/auth/login`.
- Protected routes use `get_current_user` or `get_current_admin` dependency.
- App-side auth persistence is session-only (`sessionStorage`).
- Closing tab/window removes login state for next reopen.

### Admin panel auth

- Session-cookie based, independent from API bearer tokens.
- Admin login stores `admin_user_id` in session.
- Every admin route checks `_load_admin_user(...)`.
- Frontend inactivity timer logs out admin after 2 minutes.

## 4) Data model architecture

Core tables:

- `users`
- `messages`
- `message_attachments`
- `app_settings`

Important relations:

- `users (1) -> (many) messages`
- `messages (1) -> (many) message_attachments`
- `messages.parent_message_id -> messages.id` (reply reference)

## 5) Upload architecture

- Files are uploaded via multipart `POST /api/messages`.
- Backend validates **total selected upload size** against current configured limit.
- Files are saved with generated storage names (not raw client path/name).
- Metadata is saved per attachment row.
- Attachment availability can be disabled per attachment (`is_available=false`) while preserving message history.

## 6) Presence architecture

- Presence is in-memory (`presence.py`) and heartbeat-based.
- Authenticated calls refresh `last_seen`.
- Online timeout removes stale users.
- Sidebar uses `/api/users/presence` polling to show online/offline.

## 7) Deployment architecture

Docker compose services:

- `mysql` container
- `server` container

Persistent volumes:

- `mysql_data` -> DB state
- `chat_uploads` -> upload files

This keeps messages/users/files persistent across restart/recreate.

## 8) Design philosophy

- Keep architecture explicit and understandable.
- Prefer modular Python files over monolith.
- Keep behavior predictable for learning and project defense.
