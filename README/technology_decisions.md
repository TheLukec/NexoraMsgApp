# Technology Decisions

This document explains why the project uses specific technologies and structure.

## Why Python backend

- Fast development speed and readable syntax.
- Strong ecosystem for web backends (FastAPI, Flask, SQLAlchemy).
- Suitable for teaching because code stays compact and explicit.
- Easy onboarding for students and teams.

## Why JavaScript frontend

- Browser-native language for interactive UI behavior.
- Simple direct API integration via `fetch`.
- No heavy frontend framework needed for this project scope.
- Easy to inspect and demonstrate in browser developer tools.

## Why MySQL

- Reliable relational database for user/message data.
- Good support in Docker ecosystem.
- Common in production and education contexts.
- Natural fit for structured tables and joins.

## Why Docker for server side

- One-command startup for backend + database.
- Reduces "works on my machine" setup problems.
- Keeps runtime consistent across environments.
- Simplifies deployment progression later.

## Why split into `app` and `server`

- Clear separation of concerns:
  - `app` handles local client UX.
  - `server` handles shared data and authentication.
- Enables multiple users to connect to one host.
- Easier to evolve frontend and backend independently.
- Better architecture for demonstrating client-server model.

## Why FastAPI for server

- Typed request models with Pydantic.
- Dependency injection for auth and DB sessions.
- Clean modular route design.
- Strong docs/testing friendliness for future upgrades.

## Why Flask for local app

- Very lightweight and simple for serving static/template UI.
- Minimal moving parts for local launcher.
- Ideal when frontend logic mostly lives in JavaScript.

## Why JWT for API auth and session for admin panel

- JWT is practical for stateless API calls from client app.
- Session cookies are practical for server-rendered admin forms.
- This mixed approach keeps each surface simple for its use case.

## Why modular file organization

- Easier maintenance and focused responsibility per file.
- Lower risk of merge conflicts and accidental coupling.
- Better for explaining project architecture to others.
- Makes incremental upgrades predictable.
