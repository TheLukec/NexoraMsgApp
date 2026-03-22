from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, selectinload

from auth import hash_password, verify_password
from chat_settings import (
    get_upload_limit_mb,
    get_uploads_enabled,
    set_upload_limit_mb,
    set_uploads_enabled,
)
from database import get_db
from models import Message, MessageAttachment, User
from presence import mark_inactive
from upload_service import delete_stored_file, resolve_upload_path
from user_cleanup import delete_user_with_related_data

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["Admin"])

ATTACHMENT_REMOVED_BY_ADMIN_TEXT = "Attachment was removed by admin"
FILE_NO_LONGER_AVAILABLE_TEXT = "File no longer available on server"


def _load_admin_user(request: Request, db: Session) -> User | None:
    admin_user_id = request.session.get("admin_user_id")
    if not admin_user_id:
        return None
    admin_user = db.get(User, int(admin_user_id))
    if admin_user is None or not admin_user.is_admin:
        request.session.clear()
        return None
    return admin_user


def _storage_exists(storage_key: str | None) -> bool:
    if not storage_key:
        return False

    try:
        file_path = resolve_upload_path(storage_key)
    except Exception:
        return False

    return file_path.exists()


def _message_rows(db: Session, limit: int = 300):
    return db.execute(
        select(Message, User.username)
        .join(User, Message.user_id == User.id)
        .options(selectinload(Message.attachments))
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).all()


def _message_attachment_payload(message: Message) -> list[dict]:
    if message.attachments:
        payload: list[dict] = []
        for attachment in message.attachments:
            storage_key = attachment.stored_name or attachment.file_path
            exists_on_disk = _storage_exists(storage_key)
            is_available = bool(attachment.is_available) and exists_on_disk

            availability_message = None
            if not bool(attachment.is_available):
                availability_message = ATTACHMENT_REMOVED_BY_ADMIN_TEXT
            elif not exists_on_disk:
                availability_message = FILE_NO_LONGER_AVAILABLE_TEXT

            payload.append(
                {
                    "id": attachment.id,
                    "file_name": attachment.original_name,
                    "file_path": storage_key,
                    "file_size": attachment.file_size,
                    "mime_type": attachment.mime_type,
                    "file_download_path": (f"/admin/uploads/attachments/{attachment.id}" if is_available else None),
                    "available": is_available,
                    "availability_message": availability_message,
                }
            )

        return payload

    if message.file_original_name:
        storage_key = (message.file_storage_name or "").strip()
        exists_on_disk = _storage_exists(storage_key)
        is_available = bool(storage_key) and exists_on_disk

        availability_message = None
        if not storage_key:
            availability_message = ATTACHMENT_REMOVED_BY_ADMIN_TEXT
        elif not exists_on_disk:
            availability_message = FILE_NO_LONGER_AVAILABLE_TEXT

        return [
            {
                "id": None,
                "file_name": message.file_original_name,
                "file_path": storage_key,
                "file_size": message.file_size,
                "mime_type": message.file_mime_type,
                "file_download_path": (f"/admin/uploads/{message.id}" if is_available else None),
                "available": is_available,
                "availability_message": availability_message,
            }
        ]

    return []


def _collect_all_upload_storage_keys(db: Session) -> set[str]:
    stored_file_names: set[str] = set()

    attachment_rows = db.execute(
        select(MessageAttachment.stored_name, MessageAttachment.file_path)
    ).all()
    for stored_name, file_path in attachment_rows:
        storage_key = (stored_name or file_path or "").strip()
        if storage_key:
            stored_file_names.add(storage_key)

    legacy_storage_names = db.scalars(
        select(Message.file_storage_name).where(Message.file_storage_name.is_not(None))
    ).all()
    for legacy_storage_name in legacy_storage_names:
        if legacy_storage_name:
            stored_file_names.add(legacy_storage_name)

    return stored_file_names


def _clear_all_messages_and_uploads(db: Session) -> tuple[int, int, int]:
    """Delete all chat messages + attachment rows + physical files."""
    stored_file_names = _collect_all_upload_storage_keys(db)
    messages_total = db.scalar(select(func.count(Message.id))) or 0
    attachments_total = db.scalar(select(func.count(MessageAttachment.id))) or 0

    try:
        db.execute(delete(MessageAttachment))
        db.execute(delete(Message))
        db.commit()
    except Exception:
        db.rollback()
        raise

    for stored_file_name in stored_file_names:
        delete_stored_file(stored_file_name)

    return messages_total, attachments_total, len(stored_file_names)


def _clear_all_uploads_only(db: Session) -> tuple[int, int, int]:
    """Delete physical upload files but keep message rows in chat history."""
    stored_file_names = _collect_all_upload_storage_keys(db)
    attachments_total = db.scalar(select(func.count(MessageAttachment.id))) or 0
    legacy_rows_total = db.scalar(
        select(func.count(Message.id)).where(Message.file_storage_name.is_not(None))
    ) or 0

    try:
        # Keep attachment rows, but mark them as unavailable for UI/download logic.
        db.execute(update(MessageAttachment).values(is_available=False))

        # For legacy single-file metadata, remove storage pointer but keep filename metadata.
        db.execute(
            update(Message)
            .where(Message.file_storage_name.is_not(None))
            .values(file_storage_name=None)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    for stored_file_name in stored_file_names:
        delete_stored_file(stored_file_name)

    return attachments_total, legacy_rows_total, len(stored_file_names)


@router.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})


@router.post("/admin/login")
def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.username == username.strip()))
    if user is None or not user.is_admin or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Invalid admin credentials"},
        )

    request.session["admin_user_id"] = user.id
    request.session["admin_username"] = user.username
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/admin/messages")
def admin_messages(request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return JSONResponse(status_code=401, content={"detail": "Admin login required"})

    rows = _message_rows(db)
    return [
        {
            "id": message.id,
            "username": username,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "attachments": _message_attachment_payload(message),
        }
        for message, username in rows
    ]


@router.get("/admin")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    users = db.scalars(select(User).order_by(User.id.asc())).all()
    messages = _message_rows(db)
    users_total = len(users)
    messages_total = db.scalar(select(func.count(Message.id))) or 0
    latest_message_at = db.scalar(select(Message.created_at).order_by(Message.created_at.desc()).limit(1))
    max_upload_mb = get_upload_limit_mb(db)
    uploads_enabled = get_uploads_enabled(db)
    notice = request.query_params.get("notice", "")

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "notice": notice,
            "admin_user": admin_user,
            "users": users,
            "messages": messages,
            "users_total": users_total,
            "messages_total": messages_total,
            "latest_message_at": latest_message_at,
            "max_upload_mb": max_upload_mb,
            "uploads_enabled": uploads_enabled,
        },
    )


@router.post("/admin/settings/upload-limit")
def admin_set_upload_limit(
    request: Request,
    max_upload_mb: str = Form(...),
    db: Session = Depends(get_db),
):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    raw = (max_upload_mb or "").strip()
    if not raw:
        return RedirectResponse(url="/admin?notice=" + quote("Upload limit is required"), status_code=303)

    try:
        parsed = int(raw)
        set_upload_limit_mb(db, parsed)
    except ValueError as error:
        return RedirectResponse(url="/admin?notice=" + quote(str(error)), status_code=303)

    return RedirectResponse(url="/admin?notice=" + quote(f"Upload limit updated to {parsed} MB"), status_code=303)


@router.post("/admin/uploads/toggle")
def admin_toggle_uploads(
    request: Request,
    uploads_enabled: str = Form(...),
    db: Session = Depends(get_db),
):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    normalized = (uploads_enabled or "").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        desired_state = True
    elif normalized in {"0", "false", "no", "off"}:
        desired_state = False
    else:
        return RedirectResponse(url="/admin?notice=" + quote("Invalid uploads toggle value"), status_code=303)

    set_uploads_enabled(db, desired_state)
    status_text = "enabled" if desired_state else "disabled"
    return RedirectResponse(url="/admin?notice=" + quote(f"File uploads {status_text}"), status_code=303)


@router.post("/admin/clear-messages")
def admin_clear_messages(request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        messages_deleted, attachments_deleted, files_deleted = _clear_all_messages_and_uploads(db)
    except Exception:
        return RedirectResponse(
            url="/admin?notice=" + quote("Failed to clear messages and attachments"),
            status_code=303,
        )

    notice = (
        "All messages and attachments deleted "
        f"({messages_deleted} messages, {attachments_deleted} attachment rows, {files_deleted} files)"
    )
    return RedirectResponse(url="/admin?notice=" + quote(notice), status_code=303)


@router.post("/admin/clear-uploads")
def admin_clear_uploads(request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        attachments_marked, legacy_rows_updated, files_deleted = _clear_all_uploads_only(db)
    except Exception:
        return RedirectResponse(
            url="/admin?notice=" + quote("Failed to clear uploads"),
            status_code=303,
        )

    notice = (
        "All uploads cleared. Messages kept "
        f"({attachments_marked} attachments marked unavailable, "
        f"{legacy_rows_updated} legacy rows updated, {files_deleted} files deleted)"
    )
    return RedirectResponse(url="/admin?notice=" + quote(notice), status_code=303)


@router.post("/admin/users/create")
def admin_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    username = username.strip()
    password = password.strip()

    if len(username) < 3:
        return RedirectResponse(url="/admin?notice=" + quote("Username must be at least 3 characters"), status_code=303)
    if len(password) < 6:
        return RedirectResponse(url="/admin?notice=" + quote("Password must be at least 6 characters"), status_code=303)

    existing_user = db.scalar(select(User).where(User.username == username))
    if existing_user:
        return RedirectResponse(url="/admin?notice=" + quote("Username already exists"), status_code=303)

    new_user = User(
        username=username,
        password_hash=hash_password(password),
        is_admin=(is_admin == "on"),
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/admin?notice=" + quote(f"User '{username}' created"), status_code=303)


@router.post("/admin/change-password")
def admin_change_password(
    request: Request,
    username: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    username = username.strip()
    new_password = new_password.strip()

    if len(new_password) < 6:
        return RedirectResponse(url="/admin?notice=" + quote("New password must be at least 6 characters"), status_code=303)

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        return RedirectResponse(url="/admin?notice=" + quote("User not found"), status_code=303)

    # Password is never stored in plain text.
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()

    mark_inactive(user.id)

    return RedirectResponse(url="/admin?notice=" + quote(f"Password changed for '{username}'"), status_code=303)


@router.get("/admin/uploads/attachments/{attachment_id}")
def admin_download_attachment_file(attachment_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    attachment = db.get(MessageAttachment, attachment_id)
    if attachment is None:
        return RedirectResponse(url="/admin?notice=" + quote("File not found"), status_code=303)

    if not attachment.is_available:
        return RedirectResponse(url="/admin?notice=" + quote(ATTACHMENT_REMOVED_BY_ADMIN_TEXT), status_code=303)

    storage_key = attachment.stored_name or attachment.file_path
    file_path = resolve_upload_path(storage_key)
    if not file_path.exists():
        return RedirectResponse(url="/admin?notice=" + quote(FILE_NO_LONGER_AVAILABLE_TEXT), status_code=303)

    return FileResponse(
        path=file_path,
        filename=attachment.original_name or file_path.name,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.get("/admin/uploads/{message_id}")
def admin_download_message_file(message_id: int, request: Request, db: Session = Depends(get_db)):
    """Legacy admin download endpoint for single-file messages."""
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    message = db.scalar(
        select(Message)
        .options(selectinload(Message.attachments))
        .where(Message.id == message_id)
    )
    if message is None:
        return RedirectResponse(url="/admin?notice=" + quote("File not found"), status_code=303)

    if message.attachments:
        attachment = message.attachments[0]
        if not attachment.is_available:
            return RedirectResponse(url="/admin?notice=" + quote(ATTACHMENT_REMOVED_BY_ADMIN_TEXT), status_code=303)

        storage_key = attachment.stored_name or attachment.file_path
        original_name = attachment.original_name
        mime_type = attachment.mime_type
    elif message.file_storage_name:
        storage_key = message.file_storage_name
        original_name = message.file_original_name
        mime_type = message.file_mime_type
    elif message.file_original_name:
        return RedirectResponse(url="/admin?notice=" + quote(ATTACHMENT_REMOVED_BY_ADMIN_TEXT), status_code=303)
    else:
        return RedirectResponse(url="/admin?notice=" + quote("File not found"), status_code=303)

    file_path = resolve_upload_path(storage_key)
    if not file_path.exists():
        return RedirectResponse(url="/admin?notice=" + quote(FILE_NO_LONGER_AVAILABLE_TEXT), status_code=303)

    return FileResponse(
        path=file_path,
        filename=original_name or file_path.name,
        media_type=mime_type or "application/octet-stream",
    )


@router.post("/admin/messages/{message_id}/delete")
def admin_delete_message(message_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    message = db.scalar(
        select(Message)
        .options(selectinload(Message.attachments))
        .where(Message.id == message_id)
    )
    if message is None:
        return RedirectResponse(url="/admin?notice=" + quote("Message not found"), status_code=303)

    stored_file_names = {
        (attachment.stored_name or attachment.file_path)
        for attachment in message.attachments
        if (attachment.stored_name or attachment.file_path)
    }
    if message.file_storage_name:
        stored_file_names.add(message.file_storage_name)

    db.delete(message)
    db.commit()

    for stored_file_name in stored_file_names:
        delete_stored_file(stored_file_name)

    return RedirectResponse(url="/admin?notice=" + quote("Message deleted"), status_code=303)


@router.post("/admin/users/{user_id}/delete")
def admin_delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    if admin_user.id == user_id:
        return RedirectResponse(url="/admin?notice=" + quote("Cannot delete the currently logged in admin"), status_code=303)

    user = db.get(User, user_id)
    if user is None:
        return RedirectResponse(url="/admin?notice=" + quote("User not found"), status_code=303)

    try:
        summary = delete_user_with_related_data(db, user)
    except Exception:
        return RedirectResponse(
            url="/admin?notice=" + quote("Failed to delete user and associated data"),
            status_code=303,
        )

    notice = (
        f"User '{summary.username}' and all associated messages/files deleted "
        f"({summary.deleted_messages} messages, {summary.deleted_files} files)"
    )
    return RedirectResponse(url="/admin?notice=" + quote(notice), status_code=303)
