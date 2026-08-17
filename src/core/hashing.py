from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_file_hash(file_path: str | Path) -> str:
    """Return MD5 hash based on full file contents."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError):
        return ""

