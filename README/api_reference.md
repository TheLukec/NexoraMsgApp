# API Reference

Base URL (default local server): `http://localhost:8000`

All API routes below are under `/api` unless explicitly marked as admin-panel web route.

## 1) Health and Auth

### `GET /api/health`

Returns basic server status.

Response example:

```json
{
  "status": "ok",
  "utc_time": "2026-03-23T10:00:00+00:00"
}
```

### `POST /api/auth/login`

Body:

```json
{
  "username": "luka",
  "password": "secret123"
}
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "luka",
    "is_admin": false,
    "created_at": "2026-03-23T10:00:00"
  }
}
```

### `POST /api/auth/logout`

Requires bearer token. Marks user inactive in presence state.

## 2) User profile and password

### `GET /api/me`

Returns authenticated user profile.

### `POST /api/user/change-password`

Body:

```json
{
  "current_password": "old12345",
  "new_password": "new12345"
}
```

## 3) Settings

### `GET /api/settings/upload-limit`

Returns current upload policy for UI sync.

Response:

```json
{
  "max_upload_mb": 10,
  "uploads_enabled": true
}
```

## 4) Messages

### `GET /api/messages?limit=120`

Returns message list with reply and attachment metadata.

Response item example:

```json
{
  "id": 22,
  "content": "See you.",
  "created_at": "2026-03-23T10:00:00",
  "username": "luka",
  "parent_message_id": 15,
  "reply_to": {
    "id": 15,
    "author": "marko",
    "content": "Coming at 8",
    "deleted": false
  },
  "attachments": [
    {
      "id": 5,
      "file_name": "report.pdf",
      "file_path": "ab12...cd.pdf",
      "file_size": 124000,
      "mime_type": "application/pdf",
      "file_download_path": "/api/uploads/attachments/5",
      "available": true,
      "availability_message": null
    }
  ]
}
```

### `POST /api/messages` (multipart/form-data)

Fields:

- `content` (optional text)
- `parent_message_id` (optional int)
- `files` (zero or more file parts)

Rules:

- text-only, files-only, or text+files allowed,
- total upload size validated against current limit,
- upload blocked when `uploads_enabled=false`.

### `DELETE /api/messages/{message_id}`

Allowed for:

- message author,
- admin.

Returns 403 when unauthorized.

## 5) Attachments download

### `GET /api/uploads/attachments/{attachment_id}`

Downloads attachment if available.

### `GET /api/uploads/{message_id}`

Legacy compatibility endpoint for older single-file behavior.

Possible attachment errors:

- `410` with `Attachment was removed by admin`
- `404` with `File no longer available on server`

## 6) Presence and user management

### `GET /api/users/presence`

Returns all users with online flag.

Response example:

```json
[
  { "username": "luka", "online": true },
  { "username": "marko", "online": false }
]
```

### Admin-only API endpoints (bearer admin)

- `GET /api/users`
- `POST /api/users`
- `DELETE /api/users/{user_id}`
- `POST /api/admin/change-password`
- `GET /api/stats`

## 7) Admin panel web routes (session-based, not `/api`)

These are form/template routes from `server/admin.py`:

- `GET /admin/login`
- `POST /admin/login`
- `GET /admin/logout`
- `GET /admin`
- `GET /admin/messages`
- `POST /admin/users/create`
- `POST /admin/users/{user_id}/delete`
- `POST /admin/messages/{message_id}/delete`
- `POST /admin/change-password`
- `POST /admin/settings/upload-limit`
- `POST /admin/uploads/toggle`
- `POST /admin/clear-messages`
- `POST /admin/clear-uploads`
- `GET /admin/uploads/attachments/{attachment_id}`
- `GET /admin/uploads/{message_id}`

## 8) Auth requirements summary

- Bearer token required for protected `/api` routes.
- Admin bearer required for admin-level `/api` routes.
- Admin panel (`/admin/...`) uses session cookie and server-side checks.
