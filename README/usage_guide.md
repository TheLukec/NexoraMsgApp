# Usage Guide

## 1) Roles

- `Admin` (server owner/operator)
- `User` (regular chat participant)

## 2) Admin workflow

1. Open `http://<server-host>:8000/admin/login`.
2. Login as admin.
3. Create user accounts.
4. Share credentials + server address to users.
5. Monitor messages and attachments from dashboard.
6. Manage upload policy as needed.

### Admin maintenance actions

- `Clear all messages`: wipes chat history and all attachment data/files.
- `Clear all uploads`: keeps messages, removes physical files, marks attachments unavailable.
- `Disable uploads`: blocks new file uploads globally (text messages still work).

### Admin session behavior

- If no activity for 2 minutes, admin is auto logged out.
- Login page shows inactivity notice after auto logout.

## 3) User workflow

1. Start local app (`python app/main.py`).
2. In login form enter:
   - protocol,
   - domain/IP,
   - port,
   - username,
   - password.
3. Submit login.
4. Use chat features:
   - send text,
   - reply,
   - attach files,
   - delete own messages,
   - change own password.

## 4) Sending files

User can send:

- text only,
- files only,
- text + files.

Before sending:

- selected files are listed,
- each file can be removed (`X`),
- total size vs limit is shown,
- send is blocked if total exceeds current limit.

During send:

- progress indicator is shown.

After send:

- text and selected files reset.

## 5) Reply usage

- Click `Reply` on target message.
- Reply preview appears above input.
- Click `Cancel` to exit reply mode.
- Sent message stores reference to original parent message.

## 6) Upload-related notices in chat

If attachment is unavailable, chat shows a message instead of download:

- `Attachment was removed by admin`, or
- `File no longer available on server`.

## 7) Presence usage

- Users sidebar shows all registered users.
- Each user is marked online/offline.
- Presence updates periodically.

## 8) Logout/session behavior

### User app

- Session is browser-session scoped.
- Closing tab/window removes login persistence.
- Reopening app requires fresh login.

### Admin panel

- Manual logout available via dashboard.
- Auto logout after inactivity for safety.

## 9) Practical troubleshooting

### Cannot login

- verify server URL fields (protocol/domain/port),
- verify username/password,
- verify server is reachable.

### File upload rejected

- check current upload limit,
- check if uploads are disabled by admin,
- reduce total selected file size.

### Download fails

- attachment may have been removed by admin,
- file may no longer exist on server volume.

### Chat jumps while reading old messages

- current behavior should preserve scroll while you are away from bottom,
- if not, refresh and test again with latest app frontend.
