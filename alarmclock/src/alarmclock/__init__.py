"""alarmclock — library-first alarm scheduling with optional CLI."""

from alarmclock.api import AlarmService
from alarmclock.exceptions import AlarmNotFoundError, AlarmclockError, InvalidTimeError
from alarmclock.models import Alarm, AlarmStatus, Repeat
from alarmclock.parser import parse_duration, parse_time
from alarmclock.scheduler import AlarmScheduler, OnAlarmCallback
from alarmclock.store import AlarmStore, default_store_path

__version__ = "0.1.0"

__all__ = [
    "Alarm",
    "AlarmNotFoundError",
    "AlarmScheduler",
    "AlarmService",
    "AlarmStatus",
    "AlarmStore",
    "AlarmclockError",
    "InvalidTimeError",
    "OnAlarmCallback",
    "Repeat",
    "default_store_path",
    "parse_duration",
    "parse_time",
]
