from alarmclock.sounds import default_sound_path, resolve_sound_path
from alarmclock.models import Alarm
from datetime import datetime
from zoneinfo import ZoneInfo


def test_default_sound_bundled():
    path = default_sound_path()
    assert path is not None
    assert path.name == "rooster_alarm.mp3"
    assert path.is_file()


def test_resolve_uses_default_when_no_custom():
    tz = ZoneInfo("UTC")
    alarm = Alarm(
        id="x",
        fire_at=datetime(2026, 6, 3, 12, 0, tzinfo=tz),
        sound_path=None,
    )
    assert resolve_sound_path(alarm) == default_sound_path()
