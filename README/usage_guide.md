# Usage Guide

## Typical usage roles

- Server owner/admin.
- Regular chat user.

## Server owner workflow

1. Start server stack (`docker compose up --build`).
2. Open admin panel at `/admin/login`.
3. Login with default admin credentials from `.env`.
4. Create user accounts in dashboard.
5. Share server URL/IP and credentials with users.

## Regular user workflow

1. Start local `app`.
2. In browser login form enter:
   - server URL or IP
   - username
   - password
3. Submit login.
4. After successful login:
   - see current messages.
   - send new message.
   - auto-refresh receives new chat updates.

## How to create users

Use admin panel:

1. Login as admin.
2. Fill username + password in "Create User".
3. Optionally mark user as admin.
4. Click "Create User".

Alternative (API):

- `POST /api/users` with admin bearer token.

## How to remove users

Use admin panel users table and click "Delete" for target user.
Current logged-in admin cannot delete own account in one click.

## How users connect to remote server

In app login screen, user can enter:

- `http://host-ip:8000`
- or domain name URL if deployed publicly.

Example:
- `http://192.168.1.20:8000`
- `https://chat.example.com`

## Chat usage notes

- All users share one common message stream.
- Refresh button forces immediate update.
- Background polling runs every 3 seconds.
- Logout clears saved token/session in browser localStorage.

## Troubleshooting

Cannot login:
- verify username/password.
- verify server URL includes protocol (`http://` or `https://`).

Cannot load messages:
- verify server is running.
- verify token has not expired.
- check browser console/network for API errors.

Admin panel inaccessible:
- verify `server` container is up.
- verify `/admin/login` route.
- check that `SECRET_KEY` is set and stable.

Database issues:
- check MySQL container health in `docker compose ps`.
- verify `DATABASE_URL` matches MySQL credentials.
