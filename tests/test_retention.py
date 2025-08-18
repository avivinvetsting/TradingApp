from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trading.core.retention import prune_directories


def test_prune_directories_dry_run(tmp_path: Path) -> None:
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    # Set mtimes
    old_time = datetime.now(timezone.utc) - timedelta(days=10)
    new_time = datetime.now(timezone.utc)

    def set_mtime(p: Path, dt: datetime) -> None:
        ts = dt.timestamp()
        # Update both atime and mtime
        os.utime(p, (ts, ts))

    set_mtime(old_dir, old_time)
    set_mtime(new_dir, new_time)

    to_remove = prune_directories(tmp_path, keep_days=5, apply=False)
    assert old_dir in to_remove
    assert new_dir not in to_remove
