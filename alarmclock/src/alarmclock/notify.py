"""Notification protocol and default bell notifier."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Protocol

from alarmclock.models import Alarm
from alarmclock.sounds import resolve_sound_path

_sound_lock = threading.Lock()


class Notifier(Protocol):
    """Protocol for alarm notification handlers."""

    def notify(self, alarm: Alarm) -> None: ...


def play_sound(path: Path) -> bool:
    """Play an audio file; returns True if playback started (one at a time)."""
    if not path.is_file():
        return False
    with _sound_lock:
        return _play_sound_unlocked(path)


def _play_sound_unlocked(path: Path) -> bool:
    try:
        if sys.platform == "darwin":
            subprocess.run(
                ["afplay", str(path)],
                check=False,
                timeout=120,
            )
            return True
        if sys.platform.startswith("linux"):
            for cmd in (
                ["paplay", str(path)],
                ["ffplay", "-nodisp", "-autoexit", str(path)],
                ["mpv", "--no-video", str(path)],
            ):
                try:
                    subprocess.run(cmd, check=False, capture_output=True)
                    return True
                except FileNotFoundError:
                    continue
        elif sys.platform == "win32":
            import winsound

            winsound.PlaySound(str(path), winsound.SND_FILENAME)
            return True
    except (OSError, FileNotFoundError):
        pass
    return False


def desktop_notification(title: str, message: str) -> None:
    """Best-effort OS notification (macOS/Linux)."""
    try:
        if sys.platform == "darwin":
            script = (
                f'display notification "{message}" '
                f'with title "{title}" sound name "Glass"'
            )
            subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
        elif sys.platform.startswith("linux"):
            subprocess.run(
                ["notify-send", title, message],
                check=False,
                capture_output=True,
            )
    except (OSError, FileNotFoundError):
        pass


def notify_alarm(
    alarm: Alarm,
    *,
    stream=None,
    use_desktop: bool = True,
) -> None:
    """Show alarm: sound (default rooster), optional OS alert, terminal bell."""
    out = stream or sys.stdout
    label = alarm.label or "Alarm"
    when = alarm.fire_at.strftime("%H:%M — %A, %b %d, %Y")

    sound = resolve_sound_path(alarm)
    if sound:
        play_sound(sound)
    else:
        print("\a", file=out, end="", flush=True)

    if use_desktop:
        desktop_notification(f"Alarm: {label}", when)

    print(f"\n*** ALARM: {label} ***", file=out)
    print(f"    {when}", file=out)


class BellNotifier:
    """Print alarm message, play sound, and ring terminal bell."""

    def __init__(self, *, stream=None, use_desktop: bool = True) -> None:
        self._stream = stream or sys.stdout
        self._use_desktop = use_desktop

    def notify(self, alarm: Alarm) -> None:
        notify_alarm(alarm, stream=self._stream, use_desktop=self._use_desktop)
