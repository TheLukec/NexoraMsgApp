# Database Explained

## 1) Persistence stack

- Database engine: MySQL.
- ORM: SQLAlchemy 2.x.
- Session lifecycle: `database.get_db()` per request.
- Startup compatibility checks in `database.py` add missing columns for older deployments.

## 2) Tables

## `users`

Purpose:

- account identity and role.

Columns:

- `id` (PK)
- `username` (unique)
- `password_hash`
- `is_admin`
- `created_at`

## `messages`

Purpose:

- core chat stream rows.

Columns:

- `id` (PK)
- `user_id` (FK -> users)
- `content`
- `created_at`
- `parent_message_id` (nullable FK -> messages, for reply)
- `reply_to_username` (snapshot fallback)
- `reply_to_content` (snapshot fallback)
- legacy fields for older single-file compatibility:
  - `file_original_name`
  - `file_storage_name`
  - `file_size`
  - `file_mime_type`

## `message_attachments`

Purpose:

- one-to-many attachments per message.

Columns:

- `id` (PK)
- `message_id` (FK -> messages)
- `original_name`
- `stored_name`
- `file_path`
- `file_size`
- `mime_type`
- `is_available` (admin can mark unavailable without deleting message)
- `created_at`

## `app_settings`

Purpose:

- persistent server settings editable by admin.

Keys in use:

- `max_upload_bytes`
- `uploads_enabled`

## 3) Relationships

- `User 1 -> many Message`
- `Message 1 -> many MessageAttachment`
- `Message -> parent Message` (reply relation)

Delete behavior highlights:

- deleting message cascades to its `message_attachments` rows,
- deleting user can trigger controlled cleanup of user messages and attachment files,
- reply references are safely updated to avoid broken relationships.

## 4) Upload persistence strategy

- DB stores attachment metadata.
- File binary data is stored in filesystem (`UPLOADS_DIR`).
- In Docker mode, upload directory is persisted via `chat_uploads` volume.

## 5) Settings persistence strategy

- Upload limit and upload-enabled flag are DB-backed via `app_settings`.
- Server reads these settings dynamically on requests.
- Admin panel updates settings immediately; user UI sees updates on next refresh cycle.

## 6) Notes for schema changes

When changing schema:

1. update `models.py`,
2. update related response schemas (`schemas.py`),
3. update route logic (`routes.py`, `admin.py`),
4. update docs,
5. plan migration path for existing data.

Current project uses startup compatibility checks, not full migration tooling (Alembic).
