from dataclasses import dataclass

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from models import Message, MessageAttachment, User
from presence import mark_inactive
from upload_service import delete_stored_file

DELETED_REPLY_PREVIEW_TEXT = "Reply to deleted message"
UNKNOWN_REPLY_AUTHOR = "Unknown"


@dataclass(slots=True)
class UserCleanupSummary:
    username: str
    deleted_messages: int
    deleted_attachments: int
    deleted_files: int


def _normalize_storage_key(stored_name: str | None, file_path: str | None) -> str | None:
    key = (stored_name or file_path or "").strip()
    return key or None


def _is_storage_key_still_referenced(db: Session, storage_key: str) -> bool:
    attachment_refs = db.scalar(
        select(func.count(MessageAttachment.id)).where(
            (MessageAttachment.stored_name == storage_key)
            | (MessageAttachment.file_path == storage_key)
        )
    ) or 0
    if attachment_refs > 0:
        return True

    legacy_refs = db.scalar(
        select(func.count(Message.id)).where(Message.file_storage_name == storage_key)
    ) or 0
    return legacy_refs > 0


def delete_user_with_related_data(db: Session, user: User) -> UserCleanupSummary:
    """Delete a user and all account-linked data, including files on disk."""
    user_id = user.id
    username = user.username

    message_rows = db.execute(
        select(Message.id, Message.file_storage_name)
        .where(Message.user_id == user_id)
    ).all()
    message_ids = [int(message_id) for message_id, _legacy_storage_name in message_rows]

    storage_keys: set[str] = {
        legacy_storage_name
        for _message_id, legacy_storage_name in message_rows
        if legacy_storage_name
    }

    attachment_rows: list[tuple[str | None, str | None]] = []
    if message_ids:
        attachment_rows = db.execute(
            select(MessageAttachment.stored_name, MessageAttachment.file_path)
            .where(MessageAttachment.message_id.in_(message_ids))
        ).all()
        for stored_name, file_path in attachment_rows:
            storage_key = _normalize_storage_key(stored_name, file_path)
            if storage_key:
                storage_keys.add(storage_key)

    try:
        if message_ids:
            # Replies from other users should stay, but the parent reference must not break.
            # Keep a minimal fallback snapshot for older rows that may not already have one.
            db.execute(
                update(Message)
                .where(Message.parent_message_id.in_(message_ids), Message.reply_to_username.is_(None))
                .values(reply_to_username=UNKNOWN_REPLY_AUTHOR)
            )
            db.execute(
                update(Message)
                .where(Message.parent_message_id.in_(message_ids), Message.reply_to_content.is_(None))
                .values(reply_to_content=DELETED_REPLY_PREVIEW_TEXT)
            )
            db.execute(
                update(Message)
                .where(Message.parent_message_id.in_(message_ids))
                .values(parent_message_id=None)
            )

            # Explicit DB cleanup order keeps the process predictable and avoids orphan rows.
            db.execute(delete(MessageAttachment).where(MessageAttachment.message_id.in_(message_ids)))
            db.execute(delete(Message).where(Message.id.in_(message_ids)))

        db.execute(delete(User).where(User.id == user_id))
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Filesystem cleanup runs after a successful DB transaction.
    # Missing or already-removed files are safely ignored in delete_stored_file().
    deleted_file_count = 0
    for storage_key in storage_keys:
        # Safety check: never delete a file that is still referenced by other rows.
        if _is_storage_key_still_referenced(db, storage_key):
            continue

        delete_stored_file(storage_key)
        deleted_file_count += 1

    mark_inactive(user_id)

    return UserCleanupSummary(
        username=username,
        deleted_messages=len(message_ids),
        deleted_attachments=len(attachment_rows),
        deleted_files=deleted_file_count,
    )
