from __future__ import annotations

import hashlib
import re
import time
from datetime import UTC, datetime
from pathlib import Path


def generate_compact_id(file_path: str | Path) -> str:
    """
    Compact deterministic id from file timestamp + short filename hash.
    Example: 260712153045-4a2c
    """
    try:
        path = Path(file_path)
        stat = path.stat()
        timestamp = time.strftime("%y%m%d%H%M%S", time.localtime(stat.st_mtime))
        name_hash = hashlib.md5(path.name.encode("utf-8")).hexdigest()[:4]
        return f"{timestamp}-{name_hash}"
    except (OSError, ValueError):
        current_time = time.strftime("%y%m%d%H%M%S", time.localtime())
        return f"{current_time}-stub"


def generate_post_id(file_path: str | Path) -> str:
    path = Path(file_path)
    now = datetime.now(UTC)
    day = now.strftime("%Y%m%d")
    slug = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") or "post"
    short_hash = hashlib.md5(f"{path.name}:{now.isoformat()}".encode()).hexdigest()[:4]
    return f"{day}-{slug}-{short_hash}"

