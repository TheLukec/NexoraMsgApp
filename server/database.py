from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_message_columns_for_existing_databases() -> None:
    """Add message columns that may be missing on older databases."""
    inspector = inspect(engine)
    if "messages" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("messages")}
    index_names = {index.get("name") for index in inspector.get_indexes("messages")}
    foreign_keys = inspector.get_foreign_keys("messages")
    has_parent_fk = any(
        "parent_message_id" in (foreign_key.get("constrained_columns") or [])
        for foreign_key in foreign_keys
    )

    with engine.begin() as connection:
        if "parent_message_id" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN parent_message_id INTEGER NULL"))
        if "reply_to_username" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN reply_to_username VARCHAR(50) NULL"))
        if "reply_to_content" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN reply_to_content TEXT NULL"))

        if "file_original_name" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN file_original_name VARCHAR(255) NULL"))
        if "file_storage_name" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN file_storage_name VARCHAR(255) NULL"))
        if "file_size" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN file_size INTEGER NULL"))
        if "file_mime_type" not in column_names:
            connection.execute(text("ALTER TABLE messages ADD COLUMN file_mime_type VARCHAR(255) NULL"))

        if "ix_messages_parent_message_id" not in index_names:
            try:
                connection.execute(text("CREATE INDEX ix_messages_parent_message_id ON messages (parent_message_id)"))
            except SQLAlchemyError:
                # Ignore if index already exists with another generated name.
                pass

        if engine.dialect.name == "mysql" and not has_parent_fk:
            try:
                connection.execute(
                    text(
                        "ALTER TABLE messages "
                        "ADD CONSTRAINT fk_messages_parent_message_id "
                        "FOREIGN KEY (parent_message_id) REFERENCES messages(id) "
                        "ON DELETE SET NULL"
                    )
                )
            except SQLAlchemyError:
                # Keep startup robust if FK already exists with another name.
                pass


def init_db() -> None:
    import models  # Local import to avoid circular imports.

    Base.metadata.create_all(bind=engine)
    _ensure_message_columns_for_existing_databases()
