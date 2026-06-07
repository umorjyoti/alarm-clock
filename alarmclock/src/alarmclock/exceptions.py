"""Public exceptions for alarmclock."""


class AlarmclockError(Exception):
    """Base exception for alarmclock."""


class AlarmNotFoundError(AlarmclockError):
    """Raised when an alarm ID does not exist."""

    def __init__(self, alarm_id: str) -> None:
        self.alarm_id = alarm_id
        super().__init__(f"Alarm not found: {alarm_id}")


class InvalidTimeError(AlarmclockError):
    """Raised when a time or duration string cannot be parsed."""

    def __init__(self, message: str, value: str | None = None) -> None:
        self.value = value
        super().__init__(message)
