"""Bundled alarm sounds."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from alarmclock.models import Alarm

DEFAULT_SOUND_NAME = "rooster_alarm.mp3"


@lru_cache(maxsize=1)
def default_sound_path() -> Path | None:
    """Path to the bundled rooster alarm (shipped with the package)."""
    try:
        import alarmclock

        root = Path(alarmclock.__file__).resolve().parent
        path = root / "_sounds" / DEFAULT_SOUND_NAME
        if path.is_file():
            return path
    except (TypeError, ImportError):
        pass
    return None


def resolve_sound_path(alarm: Alarm) -> Path | None:
    """Custom sound on the alarm, else bundled default."""
    if alarm.sound_path:
        custom = Path(alarm.sound_path).expanduser()
        if custom.is_file():
            return custom
    return default_sound_path()
