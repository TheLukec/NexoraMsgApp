# Admin Panel Explained

## 1) Purpose

Admin panel is the operational control surface for server owner.

It is used for:

- account management,
- moderation actions,
- upload policy management,
- server maintenance actions.

## 2) Auth model

- Admin panel uses server-side session (`SessionMiddleware`).
- Login is form-based (`/admin/login`).
- Session stores `admin_user_id`.
- Protected routes verify session with `_load_admin_user(...)`.

## 3) Inactivity auto logout

- Dashboard includes frontend inactivity timer set to 2 minutes.
- Activity events that reset timer:
  - mousemove,
  - mousedown/click,
  - keydown,
  - scroll,
  - touchstart.
- Timeout triggers redirect to `/admin/logout?reason=inactive`.
- Logout route clears session and redirects to login with message:
  - `You were logged out due to inactivity`.

## 4) Dashboard sections

### Server overview

- total users,
- total messages,
- latest message timestamp,
- feedback notice area.

### Upload settings

- current upload limit display,
- current uploads enabled/disabled status,
- form for updating limit.

### Server maintenance (danger zone)

- `Clear all messages`:
  - deletes all messages,
  - deletes all attachment rows,
  - deletes physical files.
- `Clear all uploads`:
  - keeps messages,
  - marks attachments unavailable,
  - deletes physical files,
  - chat UI then shows unavailable attachment notice.
- `Disable uploads` / `Enable uploads`:
  - updates persistent setting in DB,
  - affects all future upload attempts.

### User management

- create user,
- change user password,
- delete user.

Delete user action performs deep cleanup (messages + attachments + physical files) via `user_cleanup.py`.

### Message moderation

- list recent messages,
- delete any message,
- inspect/download available attachments.

## 5) UX safeguards

- Confirmation dialogs on dangerous actions.
- Scroll position preservation after form submissions.
- Notice messages after operations.

## 6) Security boundaries

- Panel routes require admin session.
- Admin-only operations are not exposed to non-admin panel users.
- Password updates always store hashes, never plain text.
- Dangerous actions are explicit form submissions, not hidden frontend-only toggles.

## 7) Important files

- `server/admin.py`
- `server/templates/admin_login.html`
- `server/templates/admin_dashboard.html`
- `server/static/admin.css`
- `server/user_cleanup.py`
- `server/chat_settings.py`
