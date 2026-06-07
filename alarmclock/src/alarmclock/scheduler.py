"""Efficient sleep-until-next alarm scheduler."""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from alarmclock.tzutil import local_timezone
from alarmclock.models import Alarm, Repeat
from alarmclock.notify import BellNotifier, Notifier
from alarmclock.reload import register_scheduler, unregister_scheduler

if TYPE_CHECKING:
    from alarmclock.api import AlarmService

OnAlarmCallback = Callable[[Alarm], None]

# Cap sleep chunks so we reload the store periodically (external edits, clock skew).
MAX_SLEEP_CHUNK = 3600.0  # 1 hour
IDLE_POLL_INTERVAL = 300.0  # 5 min when no alarms (was 60s)


def compute_next_fire(alarm: Alarm, *, now: datetime | None = None, tz: ZoneInfo | None = None) -> datetime | None:
    """Return the next fire time for an alarm, or None if disabled."""
    if not alarm.enabled:
        return None
    zone = tz or local_timezone()
    current = now or datetime.now(zone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=zone)

    fire = alarm.fire_at
    if fire.tzinfo is None:
        fire = fire.replace(tzinfo=zone)
    else:
        fire = fire.astimezone(zone)

    if alarm.repeat == Repeat.DAILY:
        candidate = current.replace(
            hour=fire.hour,
            minute=fire.minute,
            second=fire.second,
            microsecond=0,
        )
        if candidate <= current:
            candidate += timedelta(days=1)
        return candidate

    return fire


def due_alarms(alarms: list[Alarm], *, now: datetime | None = None, tz: ZoneInfo | None = None) -> list[Alarm]:
    """Return alarms that should fire at or before now."""
    zone = tz or local_timezone()
    current = now or datetime.now(zone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=zone)

    result: list[Alarm] = []
    for alarm in alarms:
        if not alarm.enabled:
            continue
        fire = alarm.fire_at
        if fire.tzinfo is None:
            fire = fire.replace(tzinfo=zone)
        else:
            fire = fire.astimezone(zone)

        if alarm.repeat == Repeat.DAILY:
            slot = current.replace(
                hour=fire.hour,
                minute=fire.minute,
                second=0,
                microsecond=0,
            )
            if abs((current - slot).total_seconds()) <= 2.0:
                result.append(alarm)
        elif fire <= current:
            result.append(alarm)
    return result


def seconds_until_next(
    alarms: list[Alarm],
    *,
    now: datetime | None = None,
    tz: ZoneInfo | None = None,
) -> tuple[float | None, Alarm | None, datetime | None]:
    """Return (seconds, alarm, fire_at) for the nearest enabled alarm."""
    zone = tz or local_timezone()
    current = now or datetime.now(zone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=zone)

    best_seconds: float | None = None
    best_alarm: Alarm | None = None
    best_fire: datetime | None = None

    for alarm in alarms:
        next_fire = compute_next_fire(alarm, now=current, tz=zone)
        if next_fire is None:
            continue
        delta = max(0.0, (next_fire - current).total_seconds())
        if best_seconds is None or delta < best_seconds:
            best_seconds = delta
            best_alarm = alarm
            best_fire = next_fire

    return best_seconds, best_alarm, best_fire


class AlarmScheduler:
    """Block until alarms fire using event-based waiting."""

    def __init__(
        self,
        service: AlarmService,
        *,
        on_fire: OnAlarmCallback | None = None,
        notifier: Notifier | None = None,
    ) -> None:
        self._service = service
        self._on_fire = on_fire
        self._notifier = notifier or BellNotifier()
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._firing = threading.Lock()

    def wake(self) -> None:
        """Interrupt current wait to recalculate schedule."""
        self._wake.set()

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._stop.set()
        self._wake.set()

    def run(self) -> None:
        """Run scheduler loop until stop() is called."""
        register_scheduler(self)
        self._stop.clear()
        try:
            while not self._stop.is_set():
                self._tick(block=True)
        finally:
            unregister_scheduler(self)

    def start(self) -> threading.Thread:
        """Run scheduler in a background thread."""
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        return self._thread

    def _wait_interruptible(self, seconds: float) -> bool:
        """Sleep up to seconds; return True if woken early (recalculate)."""
        remaining = seconds
        while remaining > 0 and not self._stop.is_set():
            chunk = min(remaining, MAX_SLEEP_CHUNK)
            if self._wake.wait(timeout=chunk):
                self._wake.clear()
                return True
            remaining -= chunk
        return False

    def _tick(self, *, block: bool) -> None:
        self._service._store.invalidate()
        alarms = self._service.list(enabled_only=True)
        seconds, _, _ = seconds_until_next(alarms, tz=self._service.tz)

        if seconds is None:
            if block:
                self._wake.wait(timeout=IDLE_POLL_INTERVAL)
                self._wake.clear()
            return

        if block:
            self._wait_interruptible(max(0.0, seconds))

        if self._stop.is_set():
            return

        self._service._store.invalidate()
        fired = due_alarms(self._service.list(enabled_only=True), tz=self._service.tz)
        for alarm in fired:
            self._handle_fire(alarm)

    def _handle_fire(self, alarm: Alarm) -> None:
        with self._firing:
            if self._on_fire:
                self._on_fire(alarm)
            else:
                self._notifier.notify(alarm)

            if alarm.repeat == Repeat.DAILY:
                return

            if self._on_fire is None:
                try:
                    self._service.remove(alarm.id)
                except Exception:
                    pass
