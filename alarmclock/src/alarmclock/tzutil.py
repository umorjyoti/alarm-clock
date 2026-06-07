"""Timezone helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def _timezone_from_localtime_link() -> ZoneInfo | None:
    """Read IANA zone from /etc/localtime symlink (macOS, Linux)."""
    path = Path("/etc/localtime")
    if not path.exists():
        return None
    try:
        resolved = path.resolve()
    except OSError:
        return None
    parts = resolved.parts
    if "zoneinfo" not in parts:
        return None
    idx = parts.index("zoneinfo")
    key = "/".join(parts[idx + 1 :])
    if not key:
        return None
    try:
        return ZoneInfo(key)
    except Exception:
        return None


def local_timezone() -> ZoneInfo:
    """Return the system local timezone."""
    from_link = _timezone_from_localtime_link()
    if from_link is not None:
        return from_link

    try:
        return ZoneInfo("localtime")
    except Exception:
        pass

    now = datetime.now().astimezone()
    tz = now.tzinfo
    if isinstance(tz, ZoneInfo):
        return tz

    # Offset-only fallback: map common offsets (e.g. IST +05:30)
    if tz is not None and hasattr(tz, "utcoffset"):
        offset = tz.utcoffset(now)
        if offset is not None:
            total = int(offset.total_seconds())
            # India Standard Time
            if total == 19800:
                return ZoneInfo("Asia/Kolkata")

    return ZoneInfo("UTC")
