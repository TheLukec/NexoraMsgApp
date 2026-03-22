from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from auth import create_access_token, get_current_admin, get_current_user, hash_password, verify_password
from chat_settings import get_upload_limit_bytes, get_upload_limit_mb, get_uploads_enabled
from database import get_db
from models import Message, MessageAttachment, User
from presence import get_online_user_ids, mark_active, mark_inactive
from schemas import (
    AdminChangePasswordRequest,
    LoginRequest,
    MessageAttachmentOut,
    MessageOut,
    ReplyToOut,
    StatsOut,
    TokenResponse,
    UploadLimitOut,
    UserChangePasswordRequest,
    UserCreate,
    UserPresenceOut,
    UserPublic,
)
from upload_service import SavedUpload, delete_stored_file, resolve_upload_path, save_upload_files
from user_cleanup import delete_user_with_related_data

router = APIRouter(prefix="/api", tags=["API"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]

REPLY_PREVIEW_MAX_CHARS = 120
DELETED_REPLY_TEXT = "Reply to deleted message"
ATTACHMENT_REMOVED_BY_ADMIN_TEXT = "Attachment was removed by admin"
FILE_NO_LONGER_AVAILABLE_TEXT = "File no longer available on server"


def _short_reply_text(content: str) -> str:
    compact = " ".join(content.split())
    if len(compact) <= REPLY_PREVIEW_MAX_CHARS:
        return compact
    return f"{compact[: REPLY_PREVIEW_MAX_CHARS - 3].rstrip()}..."


def _reply_source_text(message: Message) -> str:
    content = (message.content or "").strip()
    if content:
        return content

    if message.attachments:
        first_attachment = message.attachments[0]
        return f"[Attachment] {first_attachment.original_name}"

    if message.file_original_name:
        return f"[Attachment] {message.file_original_name}"

    return ""


def _build_reply_preview(message: Message) -> ReplyToOut | None:
    """Build reply context for UI, including deleted-parent fallback."""
    if message.parent_message is not None:
        parent = message.parent_message
        parent_author = parent.author.username if parent.author is not None else (message.reply_to_username or "Unknown")
        preview_content = _reply_source_text(parent) or DELETED_REPLY_TEXT
        return ReplyToOut(
            id=parent.id,
            author=parent_author,
            content=_short_reply_text(preview_content),
            deleted=False,
        )

    if message.parent_message_id is not None or message.reply_to_username or message.reply_to_content:
        return ReplyToOut(
            id=message.parent_message_id,
            author=message.reply_to_username or "Unknown",
            content=message.reply_to_content or DELETED_REPLY_TEXT,
            deleted=True,
        )

    return None


def _storage_exists(storage_key: str | None) -> bool:
    if not storage_key:
        return False

    try:
        file_path = resolve_upload_path(storage_key)
    except HTTPException:
        return False

    return file_path.exists()


def _to_attachment_out(attachment: MessageAttachment) -> MessageAttachmentOut:
    storage_key = attachment.stored_name or attachment.file_path
    exists_on_disk = _storage_exists(storage_key)
    is_available = bool(attachment.is_available) and exists_on_disk

    availability_message: str | None = None
    if not bool(attachment.is_available):
        availability_message = ATTACHMENT_REMOVED_BY_ADMIN_TEXT
    elif not exists_on_disk:
        availability_message = FILE_NO_LONGER_AVAILABLE_TEXT

    return MessageAttachmentOut(
        id=attachment.id,
        file_name=attachment.original_name,
        file_path=storage_key,
        file_size=attachment.file_size,
        mime_type=attachment.mime_type,
        file_download_path=(f"/api/uploads/attachments/{attachment.id}" if is_available else None),
        available=is_available,
        availability_message=availability_message,
    )


def _legacy_attachment_out(message: Message) -> MessageAttachmentOut | None:
    if not message.file_original_name:
        return None

    storage_key = (message.file_storage_name or "").strip()
    exists_on_disk = _storage_exists(storage_key)
    is_available = bool(storage_key) and exists_on_disk

    availability_message: str | None = None
    if not storage_key:
        availability_message = ATTACHMENT_REMOVED_BY_ADMIN_TEXT
    elif not exists_on_disk:
        availability_message = FILE_NO_LONGER_AVAILABLE_TEXT

    return MessageAttachmentOut(
        id=None,
        file_name=message.file_original_name,
        file_path=storage_key,
        file_size=message.file_size or 0,
        mime_type=message.file_mime_type or "application/octet-stream",
        file_download_path=(f"/api/uploads/{message.id}" if is_available else None),
        available=is_available,
        availability_message=availability_message,
    )


def _to_message_out(message: Message) -> MessageOut:
    author_name = message.author.username if message.author is not None else "Unknown"

    attachments = [_to_attachment_out(attachment) for attachment in message.attachments]
    if not attachments:
        legacy_attachment = _legacy_attachment_out(message)
        if legacy_attachment is not None:
            attachments = [legacy_attachment]

    first_attachment = attachments[0] if attachments else None

    return MessageOut(
        id=message.id,
        content=message.content,
        created_at=message.created_at,
        username=author_name,
        parent_message_id=message.parent_message_id,
        reply_to=_build_reply_preview(message),
        attachments=attachments,
        file_name=(first_attachment.file_name if first_attachment else None),
        file_path=(first_attachment.file_path if first_attachment else None),
        file_size=(first_attachment.file_size if first_attachment else None),
        mime_type=(first_attachment.mime_type if first_attachment else None),
        file_download_path=(first_attachment.file_download_path if first_attachment else None),
    )


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "utc_time": datetime.now(timezone.utc).isoformat()}


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    username = payload.username.strip()
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Mark user as online as soon as login succeeds.
    mark_active(user.id)

    access_token = create_access_token({"sub": user.username, "is_admin": user.is_admin})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.post("/auth/logout")
def logout(current_user: CurrentUser) -> dict:
    mark_inactive(current_user.id)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserPublic)
def me(current_user: CurrentUser) -> UserPublic:
    mark_active(current_user.id)
    return UserPublic.model_validate(current_user)


@router.get("/settings/upload-limit", response_model=UploadLimitOut)
def get_upload_limit(current_user: CurrentUser, db: DbSession) -> UploadLimitOut:
    # Keep this authenticated so clients see the same dynamic limit enforced on uploads.
    mark_active(current_user.id)
    return UploadLimitOut(
        max_upload_mb=get_upload_limit_mb(db),
        uploads_enabled=get_uploads_enabled(db),
    )


@router.post("/user/change-password")
def change_own_password(payload: UserChangePasswordRequest, current_user: CurrentUser, db: DbSession) -> dict:
    mark_active(current_user.id)

    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Wrong current password")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    # Password is always stored as a bcrypt hash via passlib.
    current_user.password_hash = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()

    return {"detail": "Password changed successfully"}


@router.post("/admin/change-password")
def admin_change_password(payload: AdminChangePasswordRequest, current_admin: CurrentAdmin, db: DbSession) -> dict:
    mark_active(current_admin.id)

    username = payload.username.strip()
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()

    # Optional security signal: changed user is considered offline until next valid request.
    mark_inactive(user.id)

    return {"detail": f"Password changed for '{user.username}'"}


@router.get("/messages", response_model=list[MessageOut])
def get_messages(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[MessageOut]:
    # Polling this endpoint also acts as an online heartbeat.
    mark_active(current_user.id)

    messages = db.scalars(
        select(Message)
        .options(
            selectinload(Message.author),
            selectinload(Message.parent_message).selectinload(Message.author),
            selectinload(Message.parent_message).selectinload(Message.attachments),
            selectinload(Message.attachments),
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).all()

    messages.reverse()
    return [_to_message_out(message) for message in messages]


@router.post("/messages", response_model=MessageOut)
async def send_message(
    current_user: CurrentUser,
    db: DbSession,
    content: str = Form(default=""),
    parent_message_id: int | None = Form(default=None),
    files: list[UploadFile] | None = File(default=None),
    file: UploadFile | None = File(default=None),
) -> MessageOut:
    mark_active(current_user.id)

    message_content = (content or "").strip()
    if len(message_content) > 1000:
        raise HTTPException(status_code=400, detail="Message content is too long")

    incoming_files: list[UploadFile] = []
    if files:
        incoming_files.extend(files)
    if file is not None:
        incoming_files.append(file)

    # Ignore empty file inputs so text-only messages still work.
    upload_files = [upload_file for upload_file in incoming_files if (upload_file.filename or "").strip()]

    if not message_content and not upload_files:
        raise HTTPException(status_code=400, detail="Message content or file is required")

    parent_message: Message | None = None
    reply_to_username: str | None = None
    reply_to_content: str | None = None

    if parent_message_id is not None:
        parent_message = db.scalar(
            select(Message)
            .options(selectinload(Message.author), selectinload(Message.attachments))
            .where(Message.id == parent_message_id)
        )
        if parent_message is None:
            raise HTTPException(status_code=404, detail="Reply target message not found")

        # Keep a small snapshot so UI can still show context if target gets deleted later.
        reply_to_username = parent_message.author.username if parent_message.author is not None else "Unknown"
        reply_to_content = _short_reply_text(_reply_source_text(parent_message) or DELETED_REPLY_TEXT)

    if upload_files and not get_uploads_enabled(db):
        raise HTTPException(status_code=403, detail="File uploads are currently disabled by the server admin")

    saved_uploads: list[SavedUpload] = []
    if upload_files:
        max_upload_bytes = get_upload_limit_bytes(db)
        # Validate cumulative size of all uploaded files on the server.
        saved_uploads = await save_upload_files(upload_files, max_upload_bytes)

    try:
        message = Message(
            user_id=current_user.id,
            content=message_content,
            parent_message_id=(parent_message.id if parent_message is not None else None),
            reply_to_username=reply_to_username,
            reply_to_content=reply_to_content,
        )
        db.add(message)
        db.flush()

        if saved_uploads:
            attachment_rows = [
                MessageAttachment(
                    message_id=message.id,
                    original_name=saved_upload.original_name,
                    stored_name=saved_upload.storage_name,
                    file_path=saved_upload.file_path,
                    file_size=saved_upload.size,
                    mime_type=saved_upload.mime_type,
                    is_available=True,
                )
                for saved_upload in saved_uploads
            ]
            db.add_all(attachment_rows)

            # Keep legacy fields filled with the first attachment for older clients.
            first_attachment = saved_uploads[0]
            message.file_original_name = first_attachment.original_name
            message.file_storage_name = first_attachment.storage_name
            message.file_size = first_attachment.size
            message.file_mime_type = first_attachment.mime_type

        db.commit()
    except Exception:
        db.rollback()
        for saved_upload in saved_uploads:
            delete_stored_file(saved_upload.storage_name)
        raise

    message_row = db.scalar(
        select(Message)
        .options(
            selectinload(Message.author),
            selectinload(Message.parent_message).selectinload(Message.author),
            selectinload(Message.parent_message).selectinload(Message.attachments),
            selectinload(Message.attachments),
        )
        .where(Message.id == message.id)
    )

    if message_row is None:
        raise HTTPException(status_code=500, detail="Message was created but could not be loaded")

    return _to_message_out(message_row)


@router.get("/uploads/attachments/{attachment_id}")
def download_attachment_file(attachment_id: int, current_user: CurrentUser, db: DbSession):
    mark_active(current_user.id)

    attachment = db.get(MessageAttachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="File not found")

    if not attachment.is_available:
        raise HTTPException(status_code=410, detail=ATTACHMENT_REMOVED_BY_ADMIN_TEXT)

    storage_key = attachment.stored_name or attachment.file_path
    file_path = resolve_upload_path(storage_key)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=FILE_NO_LONGER_AVAILABLE_TEXT)

    return FileResponse(
        path=file_path,
        filename=attachment.original_name or file_path.name,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.get("/uploads/{message_id}")
def download_message_file(message_id: int, current_user: CurrentUser, db: DbSession):
    """Legacy download endpoint for clients that expect one file per message."""
    mark_active(current_user.id)

    message = db.scalar(
        select(Message)
        .options(selectinload(Message.attachments))
        .where(Message.id == message_id)
    )
    if message is None:
        raise HTTPException(status_code=404, detail="File not found")

    if message.attachments:
        attachment = message.attachments[0]
        if not attachment.is_available:
            raise HTTPException(status_code=410, detail=ATTACHMENT_REMOVED_BY_ADMIN_TEXT)

        storage_key = attachment.stored_name or attachment.file_path
        original_name = attachment.original_name
        mime_type = attachment.mime_type
    elif message.file_storage_name:
        storage_key = message.file_storage_name
        original_name = message.file_original_name
        mime_type = message.file_mime_type
    elif message.file_original_name:
        raise HTTPException(status_code=410, detail=ATTACHMENT_REMOVED_BY_ADMIN_TEXT)
    else:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = resolve_upload_path(storage_key)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=FILE_NO_LONGER_AVAILABLE_TEXT)

    return FileResponse(
        path=file_path,
        filename=original_name or file_path.name,
        media_type=mime_type or "application/octet-stream",
    )


@router.delete("/messages/{message_id}")
def delete_message(message_id: int, current_user: CurrentUser, db: DbSession) -> dict:
    mark_active(current_user.id)

    message = db.scalar(
        select(Message)
        .options(selectinload(Message.attachments))
        .where(Message.id == message_id)
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Permission check: only message author or admin can delete this message.
    if message.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    stored_file_names = {
        (attachment.stored_name or attachment.file_path)
        for attachment in message.attachments
        if (attachment.stored_name or attachment.file_path)
    }
    if message.file_storage_name:
        stored_file_names.add(message.file_storage_name)

    # Reply messages stay in chat; DB sets their parent_message_id to NULL on parent delete.
    db.delete(message)
    db.commit()

    for stored_file_name in stored_file_names:
        delete_stored_file(stored_file_name)

    return {"detail": "Message deleted"}


@router.get("/users/presence", response_model=list[UserPresenceOut])
def get_users_presence(current_user: CurrentUser, db: DbSession) -> list[UserPresenceOut]:
    # Any authenticated request refreshes online status for that user.
    mark_active(current_user.id)

    users = db.scalars(select(User).order_by(User.username.asc())).all()
    online_user_ids = get_online_user_ids()

    return [
        UserPresenceOut(username=user.username, online=user.id in online_user_ids)
        for user in users
    ]


@router.get("/users", response_model=list[UserPublic])
def list_users(current_admin: CurrentAdmin, db: DbSession) -> list[UserPublic]:
    mark_active(current_admin.id)
    users = db.scalars(select(User).order_by(User.created_at.asc())).all()
    return [UserPublic.model_validate(user) for user in users]


@router.post("/users", response_model=UserPublic)
def create_user(payload: UserCreate, current_admin: CurrentAdmin, db: DbSession) -> UserPublic:
    mark_active(current_admin.id)

    username = payload.username.strip()
    existing_user = db.scalar(select(User).where(User.username == username))
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=username,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_admin: CurrentAdmin, db: DbSession) -> dict:
    mark_active(current_admin.id)

    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        summary = delete_user_with_related_data(db, user)
    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to delete user and associated data") from error

    return {
        "detail": f"User '{summary.username}' and all associated messages/files deleted",
        "deleted_messages": summary.deleted_messages,
        "deleted_attachments": summary.deleted_attachments,
        "deleted_files": summary.deleted_files,
    }

@router.get("/stats", response_model=StatsOut)
def get_stats(current_admin: CurrentAdmin, db: DbSession) -> StatsOut:
    mark_active(current_admin.id)

    users_total = db.scalar(select(func.count(User.id))) or 0
    messages_total = db.scalar(select(func.count(Message.id))) or 0
    return StatsOut(users_total=users_total, messages_total=messages_total)
