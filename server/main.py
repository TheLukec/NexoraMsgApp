from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from admin import router as admin_router
from auth import hash_password
from chat_settings import ensure_upload_limit_setting
from config import settings
from database import SessionLocal, init_db
from models import User
from routes import router as api_router
from upload_service import ensure_uploads_dir

BASE_DIR = Path(__file__).resolve().parent


def create_default_admin() -> None:
    db = SessionLocal()
    try:
        admin_user = db.scalar(select(User).where(User.username == settings.default_admin_username))
        if not admin_user:
            admin_user = User(
                username=settings.default_admin_username,
                password_hash=hash_password(settings.default_admin_password),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()

        # Ensure persistent server setting exists for upload size limit.
        ensure_upload_limit_setting(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_uploads_dir()
    create_default_admin()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(api_router)
app.include_router(admin_router)


@app.get("/")
def root() -> dict:
    return {
        "message": "Nexora group chat server is running",
        "admin_panel": "/admin/login",
        "api_health": "/api/health",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)

