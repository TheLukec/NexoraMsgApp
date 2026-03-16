# App Explained

## Purpose of `app`

The `app` folder contains a local client application.
Its job is to provide an easy browser interface for users.

Important: this app does not store chat data.
It only communicates with the central `server` API.

## Runtime behavior

When `python main.py` is executed:

1. Flask app starts on `APP_HOST:APP_PORT` (default `127.0.0.1:5000`).
2. Browser is opened automatically (`gui.open_in_browser`).
3. Root route renders `templates/index.html`.
4. Frontend JavaScript handles login and chat operations.

## Main files and roles

`config.py`
- Holds local host/port config.
- Controls browser auto-open behavior.

`gui.py`
- Opens the browser in a timed thread so Flask can boot first.

`main.py`
- Creates Flask app.
- Registers routes.
- Starts local server process.

`routes.py`
- Defines the `/` route.
- Returns the main HTML page.

`templates/index.html`
- Login form (server URL, username, password).
- Chat view (messages, send box, refresh/logout buttons).

`static/app.js`
- Handles all frontend logic:
- login request.
- token storage/restore.
- polling messages every 3 seconds.
- sending new messages.
- rendering message list.

`static/styles.css`
- Defines layout and visual styling for login/chat views.

## How app talks to server

The app frontend sends requests directly to server API URLs:

- Login: `POST /api/auth/login`
- Fetch messages: `GET /api/messages`
- Send message: `POST /api/messages`

Auth token from login is attached as:
`Authorization: Bearer <token>`

## Important state in frontend

`state.serverUrl`
- Which backend host is being used.

`state.token`
- JWT from login.

`state.username`
- Display name for UI info.

`state.pollTimer`
- Interval handler for periodic refresh.

## What to watch when modifying `app`

- Keep server URL normalization logic stable.
- Keep token handling consistent across requests.
- Do not trust frontend for security checks (server is authority).
- Keep polling interval reasonable to avoid server overload.
- If you add features, avoid coupling UI logic into one giant function.

## Good extension points

- Add message timestamps formatting options.
- Add connection status indicators (online/offline).
- Add retry/backoff strategy for temporary network errors.
- Add optional WebSocket mode later for real-time updates.
