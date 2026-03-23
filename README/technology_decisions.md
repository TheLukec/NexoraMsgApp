# Technology Decisions

This document explains why the current architecture and implementation choices were made.

## 1) Why Python for both runtimes

- Fast development and clear syntax.
- Easy readability for education and oral project defense.
- Strong libraries for API and DB work.
- Consistent language across app and server lowers onboarding cost.

## 2) Why FastAPI on server

- Strong typed request/response modeling (Pydantic).
- Clean dependency injection for auth and DB sessions.
- Good match for modular route-based architecture.
- Easy to extend with async upload handling.

## 3) Why Flask for local app launcher

- Lightweight and simple for serving one UI page.
- Good fit when most client logic is in browser JavaScript.
- Minimal framework overhead for local desktop-like launcher behavior.

## 4) Why vanilla JavaScript frontend

- No framework lock-in for a learning-oriented project.
- Direct control over polling, rendering, and upload state.
- Easy debugging in browser devtools.
- Lower complexity for incremental feature additions.

## 5) Why MySQL

- Reliable relational storage for users/messages/attachments/settings.
- Familiar and practical for school and small deployments.
- Works well with Docker and SQLAlchemy.

## 6) Why Docker for server stack

- One-command startup for backend + database.
- Consistent runtime across machines.
- Persistent volumes simplify operational reliability.
- Easy to demonstrate deployment basics.

## 7) Why separate `app` and `server`

- Clear separation of concerns.
- Mirrors real client-server architecture.
- Multiple users can run local app while sharing one server.
- Easier future evolution of either side without tight coupling.

## 8) Why mixed auth model (JWT + session)

- JWT for `/api` endpoints used by JS app clients.
- Session cookies for server-rendered admin panel forms.
- Practical split that keeps each UI/auth surface simple.

## 9) Why sessionStorage for user auth persistence

- Requirement: user should not stay logged in after closing tab/window.
- `sessionStorage` provides per-session persistence only.
- Prevents accidental long-lived browser auth reuse from older localStorage behavior.

## 10) Why frontend inactivity timer for admin auto logout

- Requirement-focused, simple to understand and explain.
- Immediate UX feedback and clear redirect path with notice message.
- Complements server session checks by forcing timed logout after no interaction.

## 11) Why keep compatibility fields for attachments

- Existing data and older clients may still rely on legacy single-file message fields.
- New model supports multi-file attachments cleanly.
- Compatibility layer allows safer transition without breaking all old paths at once.

## 12) Why lightweight startup DB compatibility checks

- Project currently avoids heavy migration stack complexity.
- Startup checks add missing columns for older DBs.
- Good compromise for educational context, with note to adopt Alembic later.

## 13) Why polling instead of WebSocket

- Simpler implementation and easier debugging.
- Sufficient for scope and small user count.
- Still supports required behaviors (chat refresh, settings refresh, presence updates).
