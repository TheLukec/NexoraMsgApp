# Program Flow Step by Step

This document explains important runtime scenarios with the current implementation.

## A) Server startup flow

1. `server/main.py` loads settings and creates FastAPI app.
2. Lifespan startup runs:
   - DB schema init,
   - compatibility column checks,
   - upload directory creation,
   - default admin bootstrap,
   - upload settings bootstrap (`max_upload_bytes`, `uploads_enabled`).
3. Middleware and routers are registered.
4. Server starts listening.

## B) App startup flow

1. `app/main.py` creates Flask app.
2. Local browser page is served from `app/templates/index.html`.
3. Frontend script initializes state and tries session restore from `sessionStorage`.
4. If no session data exists, login panel is shown.

## C) User login flow

1. User enters protocol + domain/IP + port + credentials.
2. Frontend builds server URL and validates input.
3. Frontend calls `POST /api/auth/login`.
4. Backend verifies password hash and returns JWT.
5. Frontend stores session data in `sessionStorage` and opens chat panel.
6. Initial data fetch loads messages, presence, and upload settings.

## D) Message refresh flow (every 3 seconds)

1. Frontend calls `GET /api/messages`.
2. Backend validates token and returns message list.
3. Frontend re-renders messages with scroll-preserve logic.
4. Frontend calls `GET /api/settings/upload-limit` to refresh current upload policy.

## E) Send message flow (with optional files)

1. User writes text and optionally selects multiple files.
2. Frontend validates:
   - not empty text/files combination,
   - selected total size against current limit,
   - upload-enabled state.
3. Frontend sends multipart `POST /api/messages`.
4. Backend validates auth and upload policy.
5. Backend saves files to disk and metadata to DB.
6. Backend stores message row and optional reply relation.
7. Frontend shows success, clears input state, refreshes messages.

## F) Reply flow

1. User clicks `Reply` on message.
2. Frontend stores target message in reply state and shows preview.
3. Send request includes `parent_message_id`.
4. Backend stores reply relation + snapshot fallback data.
5. Message list renders reply context line.

## G) Delete message flow

### User delete

1. User clicks delete on own message.
2. Frontend calls `DELETE /api/messages/{id}`.
3. Backend checks ownership/admin rights.
4. Message row is deleted.
5. Related attachment files are cleaned.

### Admin delete

1. Admin clicks delete in dashboard.
2. `POST /admin/messages/{id}/delete` executes.
3. Backend deletes message and related files.
4. Dashboard reloads with notice.

## H) Clear all uploads flow

1. Admin clicks `Clear all uploads`.
2. Backend:
   - marks attachments unavailable,
   - clears legacy file-storage pointers,
   - deletes physical files.
3. Messages remain in chat.
4. User chat shows attachment unavailable notice instead of download.

## I) Clear all messages flow

1. Admin clicks `Clear all messages`.
2. Backend removes all messages and attachment rows.
3. Backend deletes all physical upload files.
4. Chat becomes empty.

## J) Disable uploads flow

1. Admin toggles uploads state in dashboard.
2. Backend persists `uploads_enabled` in DB settings.
3. User app sees change on next refresh cycle.
4. Upload UI is disabled.
5. Backend still enforces block for upload requests.

## K) Admin inactivity auto logout flow

1. Admin dashboard JS starts 2-minute inactivity timer.
2. Mouse/keyboard/scroll/touch events reset timer.
3. If timer expires, page redirects to `/admin/logout?reason=inactive`.
4. Backend clears session and redirects to login page with notice.

## L) User reopen behavior flow

1. User closes browser tab/window.
2. Session-scoped storage is lost.
3. User opens app again later.
4. No auth session to restore; login page is shown.
