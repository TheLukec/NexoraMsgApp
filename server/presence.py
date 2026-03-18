from datetime import datetime, timedelta, timezone
from threading import Lock

# A user is considered online while the server receives periodic requests from that user.
ONLINE_TIMEOUT_SECONDS = 20

_presence_lock = Lock()
_last_seen_by_user: dict[int, datetime] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup_expired_locked(now: datetime) -> None:
    stale_cutoff = now - timedelta(seconds=ONLINE_TIMEOUT_SECONDS)
    stale_user_ids = [
        user_id
        for user_id, last_seen in _last_seen_by_user.items()
        if last_seen < stale_cutoff
    ]
    for user_id in stale_user_ids:
        _last_seen_by_user.pop(user_id, None)


def mark_active(user_id: int) -> None:
    now = _utcnow()
    with _presence_lock:
        # Online heartbeat: each valid request refreshes this timestamp.
        _last_seen_by_user[user_id] = now
        _cleanup_expired_locked(now)


def mark_inactive(user_id: int) -> None:
    with _presence_lock:
        _last_seen_by_user.pop(user_id, None)


def get_online_user_ids() -> set[int]:
    now = _utcnow()
    with _presence_lock:
        _cleanup_expired_locked(now)
        return set(_last_seen_by_user.keys())
