# Features

## 1) Chat features

- Single shared group chat stream for all users.
- Send text messages.
- Reply to existing message using `parent_message_id`.
- Reply context rendering in message list.
- Fallback rendering for deleted parent messages.
- Delete message:
  - user can delete own messages,
  - admin can delete any message.
- Polling refresh every 3 seconds for chat updates.
- Scroll stability: user is not forced to bottom while reading older messages.

## 2) User account features

- User login with server connection fields:
  - protocol (`http://` / `https://`),
  - domain or IP,
  - port.
- User logout endpoint support.
- User password change (`current_password`, `new_password`).
- Session-only auth persistence in browser (`sessionStorage`).

## 3) Presence features

- Online/offline status list in app sidebar.
- Heartbeat refresh from authenticated requests.
- In-memory timeout-based cleanup.

## 4) Upload features

- Multi-file attachment support in one message.
- Text-only, file-only, and text+files sending modes.
- File picker with selected-file list.
- Remove selected file before send (`X` button per file).
- Client-side total-size validation.
- Backend total-size validation (authoritative).
- Upload progress indicator in UI.
- Download links per attachment.
- Long filenames and long text wrapping fixes in UI.

## 5) Upload governance features

- Persistent upload size limit setting in DB (`app_settings`).
- Upload limit exposed via API and shown in app UI.
- Upload limit refresh piggybacks on message refresh cycle.
- Global upload enable/disable toggle from admin panel.
- Backend rejects upload when disabled (even if frontend bypassed).

## 6) Attachment availability features

- Attachments can be marked unavailable without deleting message.
- Message UI shows unavailability notice:
  - `Attachment was removed by admin`, or
  - `File no longer available on server`.

## 7) Admin panel features

- Session-based admin login.
- User creation and deletion.
- Admin password change for any user.
- Message list with delete action.
- Upload limit management.
- Dangerous maintenance tools:
  - clear all messages + attachments + physical files,
  - clear all uploads only (messages stay),
  - disable/enable uploads.
- Scroll position preservation after admin actions.
- Auto logout after 2 minutes inactivity.

## 8) Data cleanup features

- Deleting a user can also delete all related messages and attachments.
- Physical files are cleaned from disk where appropriate.
- Reply references are safely updated so foreign keys do not break.

## 9) Deployment features

- Dockerized MySQL + FastAPI server.
- Persistent DB and uploads volumes.
- `.env.example` provided for configuration bootstrap.
