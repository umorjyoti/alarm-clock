"""Parse time and duration strings."""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from alarmclock.exceptions import InvalidTimeError
from alarmclock.tzutil import local_timezone

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")
_UNIT = r"h|hr|hrs|hour|hours|d|day|days|m|min|mins|minute|minutes|s|sec|secs|second|seconds"
_DURATION_RE = re.compile(
    rf"^\+?\s*(\d+)\s*({_UNIT})?$",
    re.IGNORECASE,
)


def parse_time(value: str) -> time:
    """Parse HH:MM or H:MM into a time object."""
    value = value.strip()
    match = _TIME_RE.match(value)
    if not match:
        raise InvalidTimeError(
            f"Invalid time '{value}'. Use HH:MM (e.g. 07:30).",
            value=value,
        )
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        raise InvalidTimeError(
            f"Time out of range: {value}. Hour must be 0-23, minute 0-59.",
            value=value,
        )
    return time(hour, minute)


def parse_duration(value: str) -> timedelta:
    """Parse duration like 25m, 1h30m, +30m, 90s."""
    value = value.strip().lstrip("+").strip()
    if not value:
        raise InvalidTimeError("Duration cannot be empty.", value=value)

    total = timedelta()
    pattern = re.compile(
        rf"(\d+)\s*({_UNIT})",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(value))
    if not matches:
        match = _DURATION_RE.match(value)
        if match:
            amount = int(match.group(1))
            unit = (match.group(2) or "m").lower()
            return _unit_to_timedelta(amount, unit)
        raise InvalidTimeError(
            f"Invalid duration '{value}'. Use e.g. 25m, 1h30m, 90s.",
            value=value,
        )

    for m in matches:
        total += _unit_to_timedelta(int(m.group(1)), m.group(2).lower())

    remainder = pattern.sub("", value).strip()
    if remainder:
        raise InvalidTimeError(
            f"Invalid duration '{value}'. Unrecognized segment: {remainder}",
            value=value,
        )
    return total


def _unit_to_timedelta(amount: int, unit: str) -> timedelta:
    unit = unit.lower()
    if unit in ("h", "hr", "hrs", "hour", "hours"):
        return timedelta(hours=amount)
    if unit in ("d", "day", "days"):
        return timedelta(days=amount)
    if unit in ("m", "min", "mins", "minute", "minutes"):
        return timedelta(minutes=amount)
    if unit in ("s", "sec", "secs", "second", "seconds"):
        return timedelta(seconds=amount)
    raise InvalidTimeError(f"Unknown unit: {unit}")


def next_fire_datetime(
    at: time | None,
    in_duration: timedelta | None,
    *,
    now: datetime | None = None,
    tz: ZoneInfo | None = None,
) -> datetime:
    """Compute the next fire datetime from clock time or relative duration."""
    zone = tz or local_timezone()
    current = now or datetime.now(zone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=zone)

    if in_duration is not None:
        return current + in_duration

    if at is None:
        raise InvalidTimeError("Provide either a clock time (HH:MM) or a duration (--in 25m).")

    candidate = current.replace(
        hour=at.hour,
        minute=at.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= current:
        candidate += timedelta(days=1)
    return candidate
