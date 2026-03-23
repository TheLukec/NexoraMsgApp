# Project Overview

## 1) What the project does

Nexora Msg App is a simple group chat platform with two parts:

- `server`: central backend that stores users, messages, attachments, and server settings.
- `app`: local user launcher that opens browser UI and communicates with `server` API.

The system acts as a lightweight Discord-like alternative for a **single shared server chat**.

## 2) Scope and constraints

Implemented scope:

- one global group chat stream,
- user authentication,
- admin management UI,
- attachment uploads with server-side limits,
- reply, delete, and presence features.

Out-of-scope by design:

- DMs,
- channels,
- voice/video,
- reactions,
- rich moderation hierarchy.

## 3) Current feature set

### User-facing

- Login with protocol/domain-or-IP/port fields.
- Periodic message refresh (3s).
- Reply to one existing message (single-level).
- Delete own messages.
- Active users sidebar with online/offline state.
- Multi-file upload per message.
- Remove selected files before submit.
- Upload progress indicator.
- Upload limit display in UI.
- Attachment unavailable notice if file was removed.
- Password change form in app sidebar.
- Stable scroll behavior when reading older messages.

### Admin-facing

- Admin login with server-side session.
- Dashboard with stats and management forms.
- Create user / delete user.
- Change any user password.
- Delete any message.
- Change upload size limit.
- Disable/enable uploads globally.
- Clear all uploads (keep messages, mark attachments unavailable).
- Clear all messages + all attachments + physical files.
- Auto logout after 2 minutes of inactivity.
- Scroll position preservation after dashboard actions.

### Storage and operations

- MySQL persistence for users, messages, attachments, app settings.
- Upload files stored on server filesystem.
- Docker volumes for DB and uploads (`mysql_data`, `chat_uploads`).

## 4) Why this is useful for learning/presentation

- Clear separation between client app and shared server backend.
- Real-world concepts in manageable scope:
  - JWT auth,
  - session auth,
  - role checks,
  - relational data,
  - file handling,
  - admin operations,
  - Dockerized deployment.

## 5) Project status

The implementation is intentionally "simple but complete" for a classroom/demo baseline.
It is modular and ready for incremental upgrades (channels, WebSocket, tests, migrations).
