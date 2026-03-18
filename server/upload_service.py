import re
import secrets
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile

from config import settings

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(settings.uploads_dir)
if not UPLOADS_DIR.is_absolute():
    UPLOADS_DIR = (BASE_DIR / UPLOADS_DIR).resolve()

_ALLOWED_STORAGE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
_INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ -]")


@dataclass
class SavedUpload:
    original_name: str
    storage_name: str
    size: int
    mime_type: str


def ensure_uploads_dir() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_original_filename(filename: str) -> str:
    raw_name = Path(filename or "").name.strip()
    if not raw_name:
        raise HTTPException(status_code=400, detail="Invalid file name")

    safe_name = _INVALID_FILENAME_CHARS.sub("_", raw_name)
    safe_name = safe_name.strip(" .")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid file name")

    return safe_name[:180]


def _safe_suffix(filename: str) -> str:
    suffix = Path(filename).suffix[:20]
    if not suffix:
        return ""
    return "".join(char for char in suffix if char.isalnum() or char == ".")


def generate_storage_name(original_name: str) -> str:
    suffix = _safe_suffix(original_name)
    token = secrets.token_hex(16)
    return f"{token}{suffix}"


def resolve_upload_path(storage_name: str) -> Path:
    if not storage_name or not _ALLOWED_STORAGE_NAME.match(storage_name):
        raise HTTPException(status_code=404, detail="File not found")

    path = (UPLOADS_DIR / storage_name).resolve()
    if not str(path).startswith(str(UPLOADS_DIR)):
        raise HTTPException(status_code=404, detail="File not found")

    return path


def delete_stored_file(storage_name: str | None) -> None:
    if not storage_name:
        return

    try:
        path = resolve_upload_path(storage_name)
    except HTTPException:
        return

    if path.exists():
        path.unlink(missing_ok=True)


async def save_upload_file(upload_file: UploadFile, max_size_bytes: int) -> SavedUpload:
    ensure_uploads_dir()

    original_name = sanitize_original_filename(upload_file.filename or "")
    storage_name = generate_storage_name(original_name)
    destination = resolve_upload_path(storage_name)

    file_size = 0

    try:
        # Streaming write keeps memory usage low and enforces max size server-side.
        with destination.open("wb") as target:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break

                file_size += len(chunk)
                if file_size > max_size_bytes:
                    target.close()
                    destination.unlink(missing_ok=True)
                    max_mb = max(1, max_size_bytes // (1024 * 1024))
                    raise HTTPException(status_code=413, detail=f"File is too large. Limit is {max_mb} MB")

                target.write(chunk)
    finally:
        await upload_file.close()

    mime_type = (upload_file.content_type or "application/octet-stream").strip() or "application/octet-stream"
    return SavedUpload(
        original_name=original_name,
        storage_name=storage_name,
        size=file_size,
        mime_type=mime_type,
    )

