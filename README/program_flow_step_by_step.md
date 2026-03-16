# Program Flow Step by Step

This document explains what happens internally during core scenarios.

## A) What happens when server starts

1. Python loads `server/main.py`.
2. FastAPI app object is created.
3. Middleware is attached:
   - session middleware for admin panel.
   - CORS middleware for browser API calls.
4. Lifespan startup runs:
   - `init_db()` creates tables.
   - `create_default_admin()` inserts initial admin if missing.
5. API routes (`routes.py`) and admin routes (`admin.py`) are registered.
6. Server starts listening on configured host/port.

## B) What happens when app starts

1. Python loads `app/main.py`.
2. Flask app instance is created.
3. Route `/` is registered from `routes.py`.
4. `open_in_browser()` schedules browser launch.
5. Flask serves `index.html` page.
6. Browser downloads CSS and JS assets.

## C) What happens on user login (chat client)

1. User enters server URL, username, password in app UI.
2. `app/static/app.js` normalizes URL.
3. JS sends `POST /api/auth/login` to chosen server.
4. Server `routes.py::login` loads user from DB.
5. Server `auth.py::verify_password` checks hash.
6. If valid, server creates JWT via `create_access_token`.
7. Response returns token + public user info.
8. Frontend stores token in localStorage and transitions to chat view.

## D) What happens when user sends a message

1. User submits chat input form.
2. JS sends `POST /api/messages` with bearer token.
3. Server dependency `get_current_user` validates token and loads user.
4. Route validates content (non-empty after trim).
5. New `Message` row is inserted into MySQL.
6. Route returns created message payload.
7. Frontend refreshes message list.

## E) What happens when messages are refreshed

1. Every 3 seconds (or manual refresh), JS calls `GET /api/messages`.
2. Server verifies token.
3. Server queries latest messages joined with usernames.
4. Server returns ordered message list.
5. Frontend renders each message block and scrolls to bottom.

## F) What happens when admin logs in to panel

1. Admin opens `/admin/login`.
2. Login form posts credentials to `/admin/login`.
3. Server verifies:
   - user exists.
   - password hash matches.
   - `is_admin == True`.
4. Session stores `admin_user_id`.
5. Server redirects to `/admin` dashboard.

## G) What happens when admin creates a new user

1. Admin submits create-user form in dashboard.
2. Route `/admin/users/create` validates session.
3. Username/password constraints are checked.
4. Server checks for username uniqueness.
5. Password is hashed with bcrypt.
6. New `User` row is inserted.
7. Server redirects back to dashboard with status notice.

## H) What happens when admin deletes user

1. Admin clicks delete on selected user row.
2. Route `/admin/users/{id}/delete` validates session.
3. Route blocks self-delete for currently logged-in admin.
4. User row is deleted.
5. Due relationship cascade, related messages are removed as configured.
6. Dashboard reloads with result notice.
