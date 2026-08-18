from pathlib import Path

from harvest_flow_core.hashing import calculate_file_hash
from harvest_flow_core.ids import generate_compact_id
from harvest_flow_core.time_utils import now_iso, parse_iso_ts


def test_calculate_file_hash_returns_md5(tmp_path: Path) -> None:
    note = tmp_path / "a.md"
    note.write_text("hello", encoding="utf-8")
    digest = calculate_file_hash(note)
    assert len(digest) == 32


def test_generate_compact_id_has_expected_format(tmp_path: Path) -> None:
    note = tmp_path / "b.md"
    note.write_text("hello", encoding="utf-8")
    compact_id = generate_compact_id(note)
    head, tail = compact_id.split("-")
    assert len(head) == 12
    assert len(tail) == 4


def test_parse_iso_ts_accepts_now_iso() -> None:
    iso_text = now_iso()
    assert parse_iso_ts(iso_text) > 0
