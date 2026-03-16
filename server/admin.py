from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from auth import verify_password
from database import get_db
from models import Message, User

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["Admin"])


def _load_admin_user(request: Request, db: Session) -> User | None:
    admin_user_id = request.session.get("admin_user_id")
    if not admin_user_id:
        return None
    admin_user = db.get(User, int(admin_user_id))
    if admin_user is None or not admin_user.is_admin:
        request.session.clear()
        return None
    return admin_user


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


@router.get("/admin")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin_user = _load_admin_user(request, db)
    if admin_user is None:
        return RedirectResponse(url="/admin/login", status_code=303)

    users = db.scalars(select(User).order_by(User.id.asc())).all()
    users_total = len(users)
    messages_total = db.scalar(select(func.count(Message.id))) or 0
    latest_message_at = db.scalar(select(Message.created_at).order_by(Message.created_at.desc()).limit(1))
    notice = request.query_params.get("notice", "")

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "notice": notice,
            "admin_user": admin_user,
            "users": users,
            "users_total": users_total,
            "messages_total": messages_total,
            "latest_message_at": latest_message_at,
        },
    )


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

    from auth import hash_password

    new_user = User(
        username=username,
        password_hash=hash_password(password),
        is_admin=(is_admin == "on"),
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/admin?notice=" + quote(f"User '{username}' created"), status_code=303)


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

    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin?notice=" + quote(f"User '{user.username}' deleted"), status_code=303)
