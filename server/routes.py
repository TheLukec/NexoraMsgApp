from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from auth import create_access_token, get_current_admin, get_current_user, hash_password, verify_password
from chat_settings import get_upload_limit_bytes
from database import get_db
from models import Message, User
from presence import get_online_user_ids, mark_active, mark_inactive
from schemas import (
    AdminChangePasswordRequest,
    LoginRequest,
    MessageOut,
    ReplyToOut,
    StatsOut,
    TokenResponse,
    UserChangePasswordRequest,
    UserCreate,
    UserPresenceOut,
    UserPublic,
)
from upload_service import delete_stored_file, resolve_upload_path, save_upload_file

router = APIRouter(prefix="/api", tags=["API"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]

REPLY_PREVIEW_MAX_CHARS = 120
DELETED_REPLY_TEXT = "Reply to deleted message"


def _short_reply_text(content: str) -> str:
    compact = " ".join(content.split())
    if len(compact) <= REPLY_PREVIEW_MAX_CHARS:
        return compact
    return f"{compact[: REPLY_PREVIEW_MAX_CHARS - 3].rstrip()}..."


def _reply_source_text(message: Message) -> str:
    content = (message.content or "").strip()
    if content:
        return content
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


def _to_message_out(message: Message) -> MessageOut:
    author_name = message.author.username if message.author is not None else "Unknown"
    has_file = bool(message.file_storage_name)

    return MessageOut(
        id=message.id,
        content=message.content,
        created_at=message.created_at,
        username=author_name,
        parent_message_id=message.parent_message_id,
        reply_to=_build_reply_preview(message),
        file_name=message.file_original_name,
        file_path=message.file_storage_name,
        file_size=message.file_size,
        mime_type=message.file_mime_type,
        file_download_path=(f"/api/uploads/{message.id}" if has_file else None),
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
    file: UploadFile | None = File(default=None),
) -> MessageOut:
    mark_active(current_user.id)

    message_content = (content or "").strip()
    if len(message_content) > 1000:
        raise HTTPException(status_code=400, detail="Message content is too long")

    upload_file = file if file and (file.filename or "").strip() else None

    if not message_content and upload_file is None:
        raise HTTPException(status_code=400, detail="Message content or file is required")

    parent_message: Message | None = None
    reply_to_username: str | None = None
    reply_to_content: str | None = None

    if parent_message_id is not None:
        parent_message = db.get(Message, parent_message_id)
        if parent_message is None:
            raise HTTPException(status_code=404, detail="Reply target message not found")

        # Keep a small snapshot so UI can still show context if target gets deleted later.
        reply_to_username = parent_message.author.username if parent_message.author is not None else "Unknown"
        reply_to_content = _short_reply_text(_reply_source_text(parent_message) or DELETED_REPLY_TEXT)

    saved_upload = None
    if upload_file is not None:
        max_upload_bytes = get_upload_limit_bytes(db)
        # Upload size is validated on the server for security.
        saved_upload = await save_upload_file(upload_file, max_upload_bytes)

    message = Message(
        user_id=current_user.id,
        content=message_content,
        parent_message_id=(parent_message.id if parent_message is not None else None),
        reply_to_username=reply_to_username,
        reply_to_content=reply_to_content,
        file_original_name=(saved_upload.original_name if saved_upload else None),
        file_storage_name=(saved_upload.storage_name if saved_upload else None),
        file_size=(saved_upload.size if saved_upload else None),
        file_mime_type=(saved_upload.mime_type if saved_upload else None),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return _to_message_out(message)


@router.get("/uploads/{message_id}")
def download_message_file(message_id: int, current_user: CurrentUser, db: DbSession):
    mark_active(current_user.id)

    message = db.get(Message, message_id)
    if message is None or not message.file_storage_name:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = resolve_upload_path(message.file_storage_name)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=message.file_original_name or file_path.name,
        media_type=message.file_mime_type or "application/octet-stream",
    )


@router.delete("/messages/{message_id}")
def delete_message(message_id: int, current_user: CurrentUser, db: DbSession) -> dict:
    mark_active(current_user.id)

    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Permission check: only message author or admin can delete this message.
    if message.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    stored_file_name = message.file_storage_name

    # Reply messages stay in chat; DB sets their parent_message_id to NULL on parent delete.
    db.delete(message)
    db.commit()

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

    mark_inactive(user.id)
    db.delete(user)
    db.commit()
    return {"detail": f"User '{user.username}' deleted"}


@router.get("/stats", response_model=StatsOut)
def get_stats(current_admin: CurrentAdmin, db: DbSession) -> StatsOut:
    mark_active(current_admin.id)

    users_total = db.scalar(select(func.count(User.id))) or 0
    messages_total = db.scalar(select(func.count(Message.id))) or 0
    return StatsOut(users_total=users_total, messages_total=messages_total)

