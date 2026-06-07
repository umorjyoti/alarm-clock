import fcntl
import os
from pathlib import Path

import pytest

from alarmclock.daemon import lock_file, config_dir


@pytest.fixture
def isolated_lock(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "alarmclock"
    cfg.mkdir()
    store = cfg / "alarms.json"
    store.write_text('{"alarms": []}\n', encoding="utf-8")
    monkeypatch.setattr("alarmclock.daemon.default_store_path", lambda: store)
    monkeypatch.setattr("alarmclock.daemon.config_dir", lambda: cfg)
    monkeypatch.setattr("alarmclock.daemon.pid_file", lambda: cfg / "daemon.pid")
    monkeypatch.setattr("alarmclock.daemon.lock_file", lambda: cfg / "daemon.lock")
    monkeypatch.setattr("alarmclock.daemon.log_file", lambda: cfg / "daemon.log")
    return cfg / "daemon.lock"


def test_only_one_lock_holder(isolated_lock: Path):
    fh1 = open(isolated_lock, "w", encoding="utf-8")
    fcntl.flock(fh1.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    fh2 = open(isolated_lock, "w", encoding="utf-8")
    with pytest.raises(BlockingIOError):
        fcntl.flock(fh2.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    fcntl.flock(fh1.fileno(), fcntl.LOCK_UN)
    fh1.close()
    fh2.close()
