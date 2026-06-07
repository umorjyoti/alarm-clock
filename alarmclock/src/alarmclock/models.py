"""Alarm domain models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Any


class Repeat(str, Enum):
    ONCE = "once"
    DAILY = "daily"


@dataclass
class Alarm:
    """A single alarm definition."""

    id: str
    fire_at: datetime
    label: str = ""
    repeat: Repeat = Repeat.ONCE
    enabled: bool = True
    sound_path: str | None = None

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fire_at": self.fire_at.isoformat(),
            "label": self.label,
            "repeat": self.repeat.value,
            "enabled": self.enabled,
            "sound_path": self.sound_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alarm:
        return cls(
            id=data["id"],
            fire_at=datetime.fromisoformat(data["fire_at"]),
            label=data.get("label", ""),
            repeat=Repeat(data.get("repeat", Repeat.ONCE.value)),
            enabled=data.get("enabled", True),
            sound_path=data.get("sound_path"),
        )


@dataclass
class AlarmStatus:
    """Summary of alarm state for status queries."""

    total: int
    enabled_count: int
    next_alarm: Alarm | None
    next_fire_at: datetime | None
    seconds_until_next: float | None
