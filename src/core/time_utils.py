from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def get_file_created_ts(file_path: str | Path) -> float:
    """Return file creation timestamp, with ctime/mtime fallback."""
    stat = Path(file_path).stat()
    return getattr(stat, "st_birthtime", None) or stat.st_ctime or stat.st_mtime


def format_ts(ts: float | None) -> str:
    if ts is None:
        return "-"
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M")


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_iso_ts(value: str | None) -> float:
    """For sorting: timestamp string to epoch; return 0 when invalid."""
    if not value or value == "-":
        return 0.0

    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            parsed = datetime.strptime(value, fmt).replace(tzinfo=UTC)
            return parsed.timestamp()
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.timestamp()
    except ValueError:
        return 0.0

