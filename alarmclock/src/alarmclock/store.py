"""JSON persistence for alarms."""

from __future__ import annotations

import json
import os
from pathlib import Path

from alarmclock.exceptions import AlarmNotFoundError
from alarmclock.models import Alarm
from alarmclock.reload import notify_store_changed


def default_store_path() -> Path:
    """Resolve default alarm store path (XDG or ~/.config)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / ".config"
    return base / "alarmclock" / "alarms.json"


class AlarmStore:
    """Load and save alarms to a JSON file (mtime-cached reads)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_store_path()
        self._cache: list[Alarm] | None = None
        self._mtime_ns: int = -1

    def _file_mtime_ns(self) -> int:
        if not self.path.exists():
            return 0
        return self.path.stat().st_mtime_ns

    def invalidate(self) -> None:
        self._cache = None
        self._mtime_ns = -1

    def load(self) -> list[Alarm]:
        mtime = self._file_mtime_ns()
        if self._cache is not None and mtime == self._mtime_ns:
            return list(self._cache)

        if not self.path.exists():
            self._cache = []
            self._mtime_ns = 0
            return []

        raw = self.path.read_text(encoding="utf-8")
        if not raw.strip():
            self._cache = []
            self._mtime_ns = mtime
            return []

        data = json.loads(raw)
        self._cache = [Alarm.from_dict(item) for item in data.get("alarms", [])]
        self._mtime_ns = mtime
        return list(self._cache)

    def save(self, alarms: list[Alarm]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"alarms": [a.to_dict() for a in alarms]}
        self.path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        self._cache = list(alarms)
        self._mtime_ns = self._file_mtime_ns()
        notify_store_changed()

    def get_all(self) -> list[Alarm]:
        return self.load()

    def get(self, alarm_id: str) -> Alarm:
        for alarm in self.load():
            if alarm.id == alarm_id:
                return alarm
        raise AlarmNotFoundError(alarm_id)

    def add(self, alarm: Alarm) -> Alarm:
        alarms = self.load()
        alarms.append(alarm)
        self.save(alarms)
        return alarm

    def update(self, alarm: Alarm) -> Alarm:
        alarms = self.load()
        for i, existing in enumerate(alarms):
            if existing.id == alarm.id:
                alarms[i] = alarm
                self.save(alarms)
                return alarm
        raise AlarmNotFoundError(alarm.id)

    def remove(self, alarm_id: str) -> None:
        alarms = self.load()
        filtered = [a for a in alarms if a.id != alarm_id]
        if len(filtered) == len(alarms):
            raise AlarmNotFoundError(alarm_id)
        self.save(filtered)
