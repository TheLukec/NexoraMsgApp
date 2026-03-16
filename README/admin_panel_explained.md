# Admin Panel Explained

## Purpose

The admin panel provides a simple web GUI for server owner tasks:

- admin login.
- user creation.
- user deletion.
- basic server overview.

It exists so owner does not need to call raw API endpoints manually.

## Where implementation lives

- Backend routes: `server/admin.py`
- HTML templates: `server/templates/admin_login.html`, `server/templates/admin_dashboard.html`
- Styling: `server/static/admin.css`

## Session-based auth

Admin panel auth is cookie session based, not JWT based.

Flow:

1. Admin submits login form.
2. Server validates admin user credentials.
3. Server stores `admin_user_id` in session.
4. Protected admin routes verify session each request.

Why this approach:
- convenient for server-rendered pages.
- simple for forms and redirects.

## Route behavior

`GET /admin/login`
- render login page.

`POST /admin/login`
- validate credentials.
- set session.
- redirect to dashboard.

`GET /admin`
- verify active admin session.
- show stats and user list.

`POST /admin/users/create`
- verify session.
- validate form values.
- create user with hashed password.

`POST /admin/users/{id}/delete`
- verify session.
- prevent deleting currently logged-in admin.
- remove user and related messages.

`GET /admin/logout`
- clear session.

## Dashboard data shown

- total number of users.
- total number of messages.
- timestamp of latest message.
- current users table with admin flag.

## Important implementation details

- Password hashing for new users calls `auth.hash_password`.
- Admin check uses `is_admin` boolean.
- Status messages are passed via query parameter `notice`.
- Dashboard is rendered server-side with Jinja2 templates.

## What to watch when modifying admin panel

- Keep `_load_admin_user` checks in every admin route.
- Validate form inputs server-side (not only client-side HTML constraints).
- Avoid exposing secrets or password hashes in templates.
- Keep delete protections to avoid lockout scenarios.
- If adding bulk actions, add confirmation and auditing.
