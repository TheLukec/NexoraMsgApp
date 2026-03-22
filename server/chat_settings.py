from sqlalchemy.orm import Session

from config import settings
from models import AppSetting

UPLOAD_LIMIT_SETTING_KEY = "max_upload_bytes"
UPLOADS_ENABLED_SETTING_KEY = "uploads_enabled"
_BYTES_PER_MB = 1024 * 1024
_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def default_upload_limit_bytes() -> int:
    max_upload_mb = max(1, int(settings.default_max_upload_mb))
    return max_upload_mb * _BYTES_PER_MB


def default_uploads_enabled() -> bool:
    return True


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


def ensure_uploads_enabled_setting(db: Session) -> bool:
    setting = db.get(AppSetting, UPLOADS_ENABLED_SETTING_KEY)
    if setting is None:
        setting = AppSetting(
            key=UPLOADS_ENABLED_SETTING_KEY,
            value="1" if default_uploads_enabled() else "0",
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    raw_value = str(setting.value or "").strip().lower()
    if raw_value not in {"0", "1", "true", "false", "yes", "no", "on", "off"}:
        setting.value = "1"
        db.add(setting)
        db.commit()
        return True

    return raw_value in _TRUTHY_VALUES


def get_upload_limit_bytes(db: Session) -> int:
    return ensure_upload_limit_setting(db)


def get_upload_limit_mb(db: Session) -> int:
    return max(1, get_upload_limit_bytes(db) // _BYTES_PER_MB)


def get_uploads_enabled(db: Session) -> bool:
    return ensure_uploads_enabled_setting(db)


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


def set_uploads_enabled(db: Session, uploads_enabled: bool) -> bool:
    setting = db.get(AppSetting, UPLOADS_ENABLED_SETTING_KEY)
    if setting is None:
        setting = AppSetting(
            key=UPLOADS_ENABLED_SETTING_KEY,
            value="1" if uploads_enabled else "0",
        )
    else:
        setting.value = "1" if uploads_enabled else "0"

    db.add(setting)
    db.commit()
    return uploads_enabled
