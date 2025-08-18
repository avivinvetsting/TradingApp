from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List


def prune_directories(base_dir: str | Path, keep_days: int, apply: bool = False) -> List[Path]:
    base = Path(base_dir)
    if not base.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    to_remove: List[Path] = []
    for child in sorted(base.iterdir()):
        try:
            mtime = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
        except FileNotFoundError:
            continue
        if mtime < cutoff:
            to_remove.append(child)
    if apply:
        for p in to_remove:
            if p.is_dir():
                _rmtree(p)
            else:
                try:
                    p.unlink()
                except FileNotFoundError:
                    pass
    return to_remove


def _rmtree(path: Path) -> None:
    for sub in path.glob("**/*"):
        if sub.is_file():
            try:
                sub.unlink()
            except FileNotFoundError:
                pass
    # Remove directories bottom-up
    for sub in sorted((p for p in path.glob("**/*") if p.is_dir()), reverse=True):
        try:
            sub.rmdir()
        except OSError:
            pass
    try:
        path.rmdir()
    except OSError:
        pass
