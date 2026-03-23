# App Explained

## 1) App role

The `app` folder contains the local launcher UI for end users.

Responsibilities:

- serve static browser UI,
- capture server connection/login input,
- call server API endpoints,
- render chat/presence/upload state.

The app does **not** own persistent chat data; the server does.

## 2) Runtime behavior

`python main.py` does:

1. Start Flask app on `APP_HOST:APP_PORT`.
2. Optionally auto-open browser (`APP_OPEN_BROWSER=1`).
3. Serve `index.html`, `style.css`, and `app.js`.

## 3) Login UI and auth flow

Login form uses three connection fields:

- protocol (`http://` or `https://`),
- domain or IP,
- port.

Flow:

1. Build server URL from the three fields.
2. Send `POST /api/auth/login`.
3. Store token + username + server URL in `sessionStorage`.
4. Switch UI to chat panel.

Important: auth data is intentionally **session-only**.
Closing tab/window removes login persistence for next reopen.

## 4) Main frontend state (`app.js`)

Tracked client state includes:

- `serverUrl`, `token`, `username`,
- polling timers,
- current reply target,
- selected upload files,
- upload progress state,
- `maxUploadMb`, `uploadsEnabled`.

## 5) Chat rendering behavior

- Poll messages every 3 seconds.
- Render messages, reply context, and attachments.
- Show delete button only for own messages.
- Keep scroll stable when user reads older messages.
- Auto-stick to bottom only when user is already near bottom or after own send.

## 6) Reply behavior

- Clicking `Reply` stores target message in state.
- Preview box appears above input.
- Sending includes `parent_message_id`.
- Cancel clears reply target.

## 7) Upload UI behavior

- Multi-file selector via `+` button.
- Selected files listed with size and remove (`X`) action.
- Total selected size displayed and validated against current limit.
- Progress indicator shown during upload.
- If uploads disabled by admin, upload controls are disabled and explanatory text is shown.

## 8) Presence sidebar behavior

- Sidebar shows all users with online/offline indicator.
- Presence list refresh runs separately (every 8 seconds).
- Login state toggles visibility of Users and Change Password sidebar sections.

## 9) Password management in app

- User can change own password from sidebar form.
- Validates current password and confirmation match in UI.
- Calls backend endpoint for final verification/update.

## 10) Error handling style

- Network/API errors are surfaced in status area.
- 401 responses trigger logout flow and return to login panel.
- Upload validation errors shown before request when possible.

## 11) Key files

- `main.py`: Flask app startup.
- `routes.py`: root route that renders template.
- `gui.py`: delayed browser opener.
- `templates/index.html`: structure for login/chat/sidebar.
- `static/app.js`: full client logic.
- `static/style.css`: UI styling, layout, and responsive behavior.
