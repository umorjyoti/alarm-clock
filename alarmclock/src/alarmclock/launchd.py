"""macOS LaunchAgent install for auto-start on login and restart on crash."""

from __future__ import annotations

import plistlib
import subprocess
import sys
from pathlib import Path

from alarmclock.daemon import config_dir, log_file

LABEL = "com.alarmclock.daemon"


def launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def is_installed() -> bool:
    return launch_agent_path().exists()


def is_loaded() -> bool:
    if not is_installed():
        return False
    try:
        result = subprocess.run(
            ["launchctl", "list", LABEL],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and LABEL in (result.stdout or "")
    except OSError:
        return False


def _build_plist() -> dict:
    python = Path(sys.executable).resolve()
    config_dir().mkdir(parents=True, exist_ok=True)
    return {
        "Label": LABEL,
        "ProgramArguments": [str(python), "-m", "alarmclock.daemon"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 30,
        "StandardOutPath": str(log_file()),
        "StandardErrorPath": str(log_file()),
        "WorkingDirectory": str(Path.home()),
    }


def install() -> Path:
    """Install LaunchAgent (login auto-start + crash restart)."""
    path = launch_agent_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        plistlib.dump(_build_plist(), fh)

    subprocess.run(["launchctl", "unload", str(path)], capture_output=True, check=False)
    subprocess.run(["launchctl", "load", "-w", str(path)], check=True)
    return path


def uninstall() -> bool:
    """Remove LaunchAgent."""
    path = launch_agent_path()
    if not path.exists():
        return False
    subprocess.run(["launchctl", "unload", "-w", str(path)], capture_output=True, check=False)
    path.unlink(missing_ok=True)
    return True
