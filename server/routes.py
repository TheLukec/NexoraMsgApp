from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_admin, get_current_user, hash_password, verify_password
from database import get_db
from models import Message, User
from schemas import (
    LoginRequest,
    MessageCreate,
    MessageOut,
    StatsOut,
    TokenResponse,
    UserCreate,
    UserPublic,
)

router = APIRouter(prefix="/api", tags=["API"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "utc_time": datetime.now(timezone.utc).isoformat()}


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    username = payload.username.strip()
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token({"sub": user.username, "is_admin": user.is_admin})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.get("/messages", response_model=list[MessageOut])
def get_messages(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[MessageOut]:
    del current_user
    rows = db.execute(
        select(Message, User.username)
        .join(User, Message.user_id == User.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).all()
    rows.reverse()
    return [
        MessageOut(
            id=message.id,
            content=message.content,
            created_at=message.created_at,
            username=username,
        )
        for message, username in rows
    ]


@router.post("/messages", response_model=MessageOut)
def send_message(payload: MessageCreate, current_user: CurrentUser, db: DbSession) -> MessageOut:
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    message = Message(user_id=current_user.id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)

    return MessageOut(
        id=message.id,
        content=message.content,
        created_at=message.created_at,
        username=current_user.username,
    )


@router.get("/users", response_model=list[UserPublic])
def list_users(current_admin: CurrentAdmin, db: DbSession) -> list[UserPublic]:
    del current_admin
    users = db.scalars(select(User).order_by(User.created_at.asc())).all()
    return [UserPublic.model_validate(user) for user in users]


@router.post("/users", response_model=UserPublic)
def create_user(payload: UserCreate, current_admin: CurrentAdmin, db: DbSession) -> UserPublic:
    del current_admin
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
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"detail": f"User '{user.username}' deleted"}


@router.get("/stats", response_model=StatsOut)
def get_stats(current_admin: CurrentAdmin, db: DbSession) -> StatsOut:
    del current_admin
    users_total = db.scalar(select(func.count(User.id))) or 0
    messages_total = db.scalar(select(func.count(Message.id))) or 0
    return StatsOut(users_total=users_total, messages_total=messages_total)
