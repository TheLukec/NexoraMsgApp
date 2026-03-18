from sqlalchemy.orm import Session

from config import settings
from models import AppSetting

UPLOAD_LIMIT_SETTING_KEY = "max_upload_bytes"
_BYTES_PER_MB = 1024 * 1024


def default_upload_limit_bytes() -> int:
    max_upload_mb = max(1, int(settings.default_max_upload_mb))
    return max_upload_mb * _BYTES_PER_MB


def ensure_upload_limit_setting(db: Session) -> int:
    setting = db.get(AppSetting, UPLOAD_LIMIT_SETTING_KEY)
    if setting is None:
        setting = AppSetting(key=UPLOAD_LIMIT_SETTING_KEY, value=str(default_upload_limit_bytes()))
        db.add(setting)
        db.commit()
        db.refresh(setting)

    try:
        parsed = int(setting.value)
    except (TypeError, ValueError):
        parsed = default_upload_limit_bytes()
        setting.value = str(parsed)
        db.add(setting)
        db.commit()

    if parsed < _BYTES_PER_MB:
        parsed = _BYTES_PER_MB
        setting.value = str(parsed)
        db.add(setting)
        db.commit()

    return parsed


def get_upload_limit_bytes(db: Session) -> int:
    return ensure_upload_limit_setting(db)


def get_upload_limit_mb(db: Session) -> int:
    return max(1, get_upload_limit_bytes(db) // _BYTES_PER_MB)


def set_upload_limit_mb(db: Session, max_upload_mb: int) -> int:
    if max_upload_mb < 1:
        raise ValueError("Upload limit must be at least 1 MB")
    if max_upload_mb > 2048:
        raise ValueError("Upload limit cannot be greater than 2048 MB")

    max_upload_bytes = max_upload_mb * _BYTES_PER_MB
    setting = db.get(AppSetting, UPLOAD_LIMIT_SETTING_KEY)
    if setting is None:
        setting = AppSetting(key=UPLOAD_LIMIT_SETTING_KEY, value=str(max_upload_bytes))
    else:
        setting.value = str(max_upload_bytes)

    db.add(setting)
    db.commit()
    return max_upload_bytes
