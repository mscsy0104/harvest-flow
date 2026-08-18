from pathlib import Path

from harvest_flow_core.frontmatter import read_markdown_parts, write_markdown_parts


def test_read_write_markdown_parts_roundtrip(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text(
        "---\nstatus: draft\ntitle: Hello\n---\n\n본문 내용",
        encoding="utf-8",
    )

    meta, body = read_markdown_parts(note)
    assert meta["status"] == "draft"
    assert meta["title"] == "Hello"
    assert "본문 내용" in body

    meta["status"] = "published"
    write_markdown_parts(note, meta, body + "\n추가")

    re_meta, re_body = read_markdown_parts(note)
    assert re_meta["status"] == "published"
    assert "추가" in re_body
