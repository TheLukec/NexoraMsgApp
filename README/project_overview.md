# Project Overview

## What this project is

Nexora is a simple group chat system with two clearly separated parts:

- `server`: central backend that authenticates users and stores chat data.
- `app`: local client app that opens in browser and lets users chat.

The project is intentionally focused on one shared channel-like conversation.
There are no direct messages, no voice, and no file sharing.

## Main goals

- Keep architecture easy to understand for learning and presentations.
- Keep code modular so future upgrades are straightforward.
- Provide secure password storage and basic authentication.
- Provide practical admin tools for managing users.
- Make local setup easy with Docker for backend + MySQL.

## High-level architecture

The system has 3 runtime pieces:

1. Browser UI (JavaScript) inside the `app`.
2. Python backend for the local `app` (Flask) that serves HTML/CSS/JS.
3. Python backend for central `server` (FastAPI) + MySQL database.

Communication path:

1. User starts `app` locally.
2. Browser opens `http://127.0.0.1:5000`.
3. User enters server URL, username, password.
4. JS frontend sends login request to `server` API.
5. Server returns JWT token.
6. JS stores token in localStorage and uses it for chat API calls.
7. Messages are written to and read from MySQL via SQLAlchemy.

## Why app and server are separated

- It matches real-world distributed systems.
- User interface can evolve independently from server API.
- Server can run on host machine or remote VPS.
- Multiple users can connect from different client machines.

## Security model (basic)

- Passwords are never stored as plain text.
- Passwords are hashed with bcrypt via `passlib`.
- Authenticated API requests require bearer token.
- Admin-only endpoints are protected by admin checks.
- Admin panel uses server-side session cookie.

## Key limitations by design

- Single shared chat context.
- No channels, no DMs, no message editing/deleting.
- No role hierarchy beyond `is_admin`.
- No rate limiting and no production hardening layers yet.

These are acceptable for a teaching/learning base project.

## Suggested future upgrades

- Add Alembic migrations.
- Add refresh tokens and token revocation.
- Add pagination with `since_id` or timestamps.
- Add channel support (`channels` table + channel_id on messages).
- Add HTTPS and reverse proxy deployment examples.
- Add testing suite (unit + integration + API tests).
