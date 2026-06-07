"""Public AlarmService facade."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from alarmclock.tzutil import local_timezone
from alarmclock.exceptions import AlarmNotFoundError, InvalidTimeError
from alarmclock.models import Alarm, AlarmStatus, Repeat
from alarmclock.parser import next_fire_datetime, parse_duration, parse_time
from alarmclock.scheduler import AlarmScheduler, OnAlarmCallback, seconds_until_next
from alarmclock.store import AlarmStore, default_store_path
from alarmclock.notify import Notifier, BellNotifier


class AlarmService:
    """Primary API for managing and scheduling alarms."""

    def __init__(
        self,
        store_path: Path | str | None = None,
        tz: ZoneInfo | None = None,
    ) -> None:
        path = Path(store_path) if store_path else None
        self._store = AlarmStore(path)
        self.tz = tz or local_timezone()

    @property
    def store_path(self) -> Path:
        return self._store.path

    def add(
        self,
        *,
        at: time | str | None = None,
        in_: timedelta | str | None = None,
        label: str = "",
        repeat: Repeat | str = Repeat.ONCE,
        sound_path: str | None = None,
        enabled: bool = True,
    ) -> Alarm:
        """Create and persist a new alarm."""
        clock_time: time | None = None
        duration: timedelta | None = None

        if isinstance(at, str):
            clock_time = parse_time(at)
        elif at is not None:
            clock_time = at

        if isinstance(in_, str):
            duration = parse_duration(in_)
        elif in_ is not None:
            duration = in_

        if clock_time is None and duration is None:
            raise InvalidTimeError("Provide either at= (HH:MM) or in_= (duration).")

        if isinstance(repeat, str):
            try:
                repeat = Repeat(repeat.lower())
            except ValueError as exc:
                raise InvalidTimeError(
                    f"Invalid repeat '{repeat}'. Use once or daily.",
                    value=repeat,
                ) from exc

        fire_at = next_fire_datetime(clock_time, duration, tz=self.tz)
        alarm = Alarm(
            id=Alarm.new_id(),
            fire_at=fire_at,
            label=label,
            repeat=repeat,
            enabled=enabled,
            sound_path=sound_path,
        )
        return self._store.add(alarm)

    def list(self, enabled_only: bool = False) -> list[Alarm]:
        alarms = self._store.get_all()
        if enabled_only:
            return [a for a in alarms if a.enabled]
        return alarms

    def get(self, alarm_id: str) -> Alarm:
        return self._store.get(alarm_id)

    def remove(self, alarm_id: str) -> None:
        self._store.remove(alarm_id)

    def enable(self, alarm_id: str) -> Alarm:
        alarm = self.get(alarm_id)
        alarm.enabled = True
        return self._store.update(alarm)

    def disable(self, alarm_id: str) -> Alarm:
        alarm = self.get(alarm_id)
        alarm.enabled = False
        return self._store.update(alarm)

    def snooze(self, alarm_id: str, duration: timedelta | str) -> Alarm:
        if isinstance(duration, str):
            duration = parse_duration(duration)
        alarm = self.get(alarm_id)
        now = datetime.now(self.tz)
        alarm.fire_at = now + duration
        alarm.enabled = True
        return self._store.update(alarm)

    def status(self) -> AlarmStatus:
        alarms = self.list()
        enabled = self.list(enabled_only=True)
        seconds, next_alarm, next_fire = seconds_until_next(enabled, tz=self.tz)
        return AlarmStatus(
            total=len(alarms),
            enabled_count=len(enabled),
            next_alarm=next_alarm,
            next_fire_at=next_fire,
            seconds_until_next=seconds,
        )

    def create_scheduler(
        self,
        *,
        on_fire: OnAlarmCallback | None = None,
        notifier: Notifier | None = None,
    ) -> AlarmScheduler:
        return AlarmScheduler(
            self,
            on_fire=on_fire,
            notifier=notifier or BellNotifier(),
        )
