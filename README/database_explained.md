# Database Explained

## Why MySQL is used

MySQL is a practical choice for this project because:

- it is widely used and easy to run in Docker.
- it supports relational modeling for users/messages.
- it is stable and suitable for multi-user systems.

## ORM and access layer

The project uses SQLAlchemy ORM.
`database.py` defines:

- `engine` for DB connection.
- `SessionLocal` for transaction scope.
- `Base` for ORM models.
- `get_db()` dependency for route handlers.

## Current schema

### Table: `users`

Fields:
- `id` (PK)
- `username` (unique, indexed)
- `password_hash`
- `is_admin`
- `created_at`

Role:
- stores login identity.
- stores admin flag.
- links to authored messages.

### Table: `messages`

Fields:
- `id` (PK)
- `user_id` (FK to users.id)
- `content`
- `created_at`

Role:
- stores chat history in one global stream.

## Relationships

`User` 1 -> many `Message`

- In ORM: `User.messages` and `Message.author`.
- FK delete cascade allows cleanup of user messages if user is deleted.

## Data flow examples

Login:
- query `users` by username.
- verify hash in application layer.

Send message:
- insert row into `messages`.
- use current authenticated user id.

Get messages:
- join `messages` with `users` to include author usernames.

## Important constraints

- username uniqueness prevents duplicate accounts.
- password hash field must never receive plain text.
- message content has API-level max length.

## Migration strategy note

Current implementation uses `Base.metadata.create_all()`.
That is enough for initial learning project.
For production-grade evolution, add Alembic migrations.

## If you change schema later

- Update `models.py`.
- Update any affected `schemas.py` models.
- Update API handlers in `routes.py` and admin logic in `admin.py`.
- Update docs and setup instructions.
- Plan data migration for existing rows.
