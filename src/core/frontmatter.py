from __future__ import annotations

from pathlib import Path

import yaml


def parse_markdown(file_path: str | Path) -> tuple[dict | None, str | None, str | None]:
    """Split markdown into frontmatter and body for pipeline use."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                body_text = parts[2]
                meta = yaml.safe_load(yaml_text)
                return meta, body_text, yaml_text
    except (OSError, UnicodeError, ValueError, yaml.YAMLError):
        return None, None, None
    return None, None, None


def read_markdown_parts(file_path: str | Path) -> tuple[dict, str]:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    yaml_text = parts[1].strip()
    body = parts[2].lstrip("\n")
    try:
        meta = yaml.safe_load(yaml_text) or {}
    except (yaml.YAMLError, ValueError, TypeError):
        meta = {}
    return meta if isinstance(meta, dict) else {}, body


def write_markdown_parts(file_path: str | Path, meta: dict, body: str) -> None:
    path = Path(file_path)
    yaml_text = yaml.safe_dump(meta or {}, allow_unicode=True, sort_keys=False).strip()
    new_text = f"---\n{yaml_text}\n---\n\n{body.rstrip()}\n"
    path.write_text(new_text, encoding="utf-8")

