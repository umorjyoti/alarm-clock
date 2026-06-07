from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from alarmclock.models import Alarm, Repeat
from alarmclock.scheduler import compute_next_fire, due_alarms, seconds_until_next


def test_seconds_until_next():
    tz = ZoneInfo("UTC")
    now = datetime(2026, 6, 3, 10, 0, tzinfo=tz)
    alarms = [
        Alarm(id="a", fire_at=datetime(2026, 6, 3, 12, 0, tzinfo=tz), enabled=True),
        Alarm(id="b", fire_at=datetime(2026, 6, 3, 11, 0, tzinfo=tz), enabled=True),
    ]
    seconds, best, _ = seconds_until_next(alarms, now=now, tz=tz)
    assert best is not None
    assert best.id == "b"
    assert seconds == 3600.0


def test_due_once_alarm():
    tz = ZoneInfo("UTC")
    now = datetime(2026, 6, 3, 12, 0, 1, tzinfo=tz)
    alarms = [
        Alarm(
            id="a",
            fire_at=datetime(2026, 6, 3, 12, 0, tzinfo=tz),
            repeat=Repeat.ONCE,
            enabled=True,
        ),
    ]
    due = due_alarms(alarms, now=now, tz=tz)
    assert len(due) == 1
    assert due[0].id == "a"


def test_compute_next_fire_daily_rolls_forward():
    tz = ZoneInfo("UTC")
    now = datetime(2026, 6, 3, 14, 0, tzinfo=tz)
    alarm = Alarm(
        id="d",
        fire_at=datetime(2026, 6, 3, 7, 30, tzinfo=tz),
        repeat=Repeat.DAILY,
        enabled=True,
    )
    nxt = compute_next_fire(alarm, now=now, tz=tz)
    assert nxt is not None
    assert nxt.day == 4
    assert nxt.hour == 7
    assert nxt.minute == 30
