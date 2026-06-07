"""Background alarm daemon (single instance, file-locked)."""

from __future__ import annotations

import os

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from alarmclock.api import AlarmService
from alarmclock.models import Repeat
from alarmclock.notify import notify_alarm
from alarmclock.store import default_store_path

LOG_MAX_BYTES = 512_000


def config_dir() -> Path:
    return default_store_path().parent


def pid_file() -> Path:
    return config_dir() / "daemon.pid"


def lock_file() -> Path:
    return config_dir() / "daemon.lock"


def log_file() -> Path:
    return config_dir() / "daemon.log"


def read_pid() -> int | None:
    path = pid_file()
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def is_process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_running() -> bool:
    pid = read_pid()
    if pid is None:
        return False
    if not is_process_alive(pid):
        _cleanup_stale_files()
        return False
    return True


def _cleanup_stale_files() -> None:
    clear_pid()
    path = lock_file()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def write_pid(pid: int) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    pid_file().write_text(f"{pid}\n", encoding="utf-8")


def clear_pid() -> None:
    path = pid_file()
    if path.exists():
        path.unlink()


def _rotate_log_if_needed() -> None:
    path = log_file()
    if path.exists() and path.stat().st_size > LOG_MAX_BYTES:
        backup = path.with_suffix(".log.old")
        if backup.exists():
            backup.unlink()
        path.rename(backup)
        path.write_text("", encoding="utf-8")


def _log(message: str) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    _rotate_log_if_needed()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_file().open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {message}\n")


def _acquire_instance_lock():
    """Exclusive lock; only one daemon per machine. Returns lock file handle."""
    config_dir().mkdir(parents=True, exist_ok=True)
    fh = open(lock_file(), "w", encoding="utf-8")
    if fcntl is not None:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            existing = read_pid()
            msg = "Another alarmclock daemon is already running"
            if existing:
                msg += f" (PID {existing})"
            _log(msg)
            sys.exit(1)
    else:
        if is_running():
            fh.close()
            _log("Another alarmclock daemon is already running")
            sys.exit(1)
    fh.write(str(os.getpid()))
    fh.flush()
    return fh


def run_foreground() -> None:
    """Daemon main loop (invoked by background process or launchd)."""
    lock_fh = _acquire_instance_lock()
    write_pid(os.getpid())
    service = AlarmService()
    _log(f"Daemon started (PID {os.getpid()})")

    def on_fire(alarm):
        _log(f"Fired: {alarm.label or alarm.id} at {alarm.fire_at.isoformat()}")
        notify_alarm(alarm, use_desktop=True)
        if alarm.repeat == Repeat.DAILY:
            return
        try:
            service.remove(alarm.id)
            _log(f"Removed once alarm {alarm.id}")
        except Exception as exc:
            _log(f"Could not remove alarm {alarm.id}: {exc}")

    scheduler = service.create_scheduler(on_fire=on_fire)

    def handle_signal(_signum, _frame):
        scheduler.stop()
        _log("Daemon stopped")
        clear_pid()
        if fcntl is not None:
            try:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        lock_fh.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        scheduler.run()
    finally:
        clear_pid()
        if fcntl is not None:
            try:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        lock_fh.close()


def start() -> int:
    """Start scheduler in a detached background process (singleton)."""
    if is_running():
        raise RuntimeError(
            f"Daemon already running (PID {read_pid()}). Use `alarm stop` first."
        )

    config_dir().mkdir(parents=True, exist_ok=True)
    _rotate_log_if_needed()
    log = log_file().open("a", encoding="utf-8")

    proc = subprocess.Popen(
        [sys.executable, "-m", "alarmclock.daemon"],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )

    for _ in range(20):
        time.sleep(0.1)
        if proc.poll() is not None:
            raise RuntimeError(
                "Daemon failed to start. Check ~/.config/alarmclock/daemon.log"
            )
        if is_running() and read_pid() == proc.pid:
            _log(f"Daemon launched (PID {proc.pid})")
            return proc.pid

    if is_running():
        return read_pid() or proc.pid

    raise RuntimeError("Daemon did not acquire lock in time. See daemon.log")


def stop() -> bool:
    """Stop background daemon."""
    pid = read_pid()
    if pid is None or not is_process_alive(pid):
        _cleanup_stale_files()
        return False
    os.kill(pid, signal.SIGTERM)
    for _ in range(30):
        if not is_process_alive(pid):
            break
        time.sleep(0.1)
    _cleanup_stale_files()
    _log(f"Sent SIGTERM to PID {pid}")
    return True


if __name__ == "__main__":
    run_foreground()
