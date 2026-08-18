from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path

from config import (
    NOTES_DIR,
    WORKFLOW_DRAFT_DIR,
    WORKFLOW_REVIEW_REQUEST_DIR,
    WORKFLOW_PUBLISH_WAIT_DIR,
    WORKFLOW_NEEDS_FIX_DIR,
    WORKFLOW_SECOND_REVIEW_DONE_DIR,
    WORKFLOW_PUBLISHED_DIR,
    WORKFLOW_REVISE_WAIT_DIR,
    WORKFLOW_DELETE_REQUEST_DIR,
    WORKFLOW_TRASH_DIR,
)
from harvest_flow_core.frontmatter import read_markdown_parts, write_markdown_parts
from harvest_flow_core.ids import generate_post_id as core_generate_post_id

CHECKLIST_START = "<!-- HF_REVIEW_CHECKLIST_START -->"
CHECKLIST_END = "<!-- HF_REVIEW_CHECKLIST_END -->"
CHECKLIST_TEMPLATE = (
    f"{CHECKLIST_START}\n"
    "## 검수 체크리스트\n"
    "- [ ] 메시지와 제목이 일치한다\n"
    "- [ ] 사실/수치/링크를 재확인했다\n"
    "- [ ] TODO, TBD, placeholder 텍스트가 없다\n"
    "- [ ] 문단/헤더 구조가 읽기 쉽게 정리되어 있다\n"
    f"{CHECKLIST_END}\n"
)

STAGE_DRAFT = "초안"
STAGE_REVIEW_REQUEST = "검수요청"
STAGE_PUBLISH_WAIT = "출간대기"
STAGE_NEEDS_FIX = "수정필요"
STAGE_SECOND_REVIEW_DONE = "2차검수완료"
STAGE_PUBLISHED = "출간완료"
STAGE_REVISE_WAIT = "수정대기"
STAGE_DELETE_REQUEST = "삭제요청"
STAGE_TRASH = "휴지통"

WORKFLOW_STAGE_DIRS: dict[str, Path] = {
    STAGE_DRAFT: WORKFLOW_DRAFT_DIR,
    STAGE_REVIEW_REQUEST: WORKFLOW_REVIEW_REQUEST_DIR,
    STAGE_PUBLISH_WAIT: WORKFLOW_PUBLISH_WAIT_DIR,
    STAGE_NEEDS_FIX: WORKFLOW_NEEDS_FIX_DIR,
    STAGE_SECOND_REVIEW_DONE: WORKFLOW_SECOND_REVIEW_DONE_DIR,
    STAGE_PUBLISHED: WORKFLOW_PUBLISHED_DIR,
    STAGE_REVISE_WAIT: WORKFLOW_REVISE_WAIT_DIR,
    STAGE_DELETE_REQUEST: WORKFLOW_DELETE_REQUEST_DIR,
    STAGE_TRASH: WORKFLOW_TRASH_DIR,
}

# 기존 번호 없는 폴더명도 한동안 인식해 하위호환을 유지합니다.
LEGACY_WORKFLOW_STAGE_DIRS: dict[str, Path] = {
    STAGE_DRAFT: NOTES_DIR / "초안",
    STAGE_REVIEW_REQUEST: NOTES_DIR / "검수요청",
    STAGE_PUBLISH_WAIT: NOTES_DIR / "출간대기",
    STAGE_NEEDS_FIX: NOTES_DIR / "수정필요",
    STAGE_SECOND_REVIEW_DONE: NOTES_DIR / "2차검수완료",
    STAGE_PUBLISHED: NOTES_DIR / "출간완료",
    STAGE_REVISE_WAIT: NOTES_DIR / "수정대기",
    STAGE_DELETE_REQUEST: NOTES_DIR / "삭제요청",
    STAGE_TRASH: NOTES_DIR / "휴지통",
}

# 폴더 기반 워크플로우에서는 title 누락으로 막지 않고 status만 확인합니다.
REVIEW_REQUIRED_FRONTMATTER_KEYS = ("status",)
REVIEW_MIN_BODY_LENGTH = 80
REVIEW_FORBIDDEN_PATTERNS = (
    r"\bTODO\b",
    r"\bTBD\b",
    r"작성 예정",
    r"lorem ipsum",
    r"내용 추가",
)


def stage_from_path(file_path: str | Path) -> str | None:
    path = Path(file_path).resolve()
    path_parts = _normalized_path_parts(path)
    for stage, stage_dir in WORKFLOW_STAGE_DIRS.items():
        candidate_dirs = [stage_dir]
        legacy_dir = LEGACY_WORKFLOW_STAGE_DIRS.get(stage)
        if legacy_dir and legacy_dir != stage_dir:
            candidate_dirs.append(legacy_dir)
        for candidate_dir in candidate_dirs:
            candidate_parts = _normalized_path_parts(candidate_dir)
            if path_parts[: len(candidate_parts)] == candidate_parts:
                return stage
    return None


def _normalized_path_parts(path: str | Path) -> tuple[str, ...]:
    """macOS NFD/NFC 차이를 흡수하기 위해 각 path part를 NFC로 정규화합니다."""
    parts = Path(path).resolve().parts
    return tuple(unicodedata.normalize("NFC", part) for part in parts)


def _all_known_stage_dirs() -> list[Path]:
    dirs: list[Path] = []
    seen: set[Path] = set()
    for stage, stage_dir in WORKFLOW_STAGE_DIRS.items():
        for candidate in (stage_dir, LEGACY_WORKFLOW_STAGE_DIRS.get(stage)):
            if candidate is None:
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            dirs.append(candidate)
    return dirs


def build_stage_path(stage: str, filename: str) -> Path:
    target_dir = WORKFLOW_STAGE_DIRS[stage]
    return target_dir / filename


def move_note_to_stage(file_path: str | Path, stage: str) -> Path:
    src = Path(file_path)
    target = build_stage_path(stage, src.name)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.resolve() == src.resolve():
        return target

    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        target = target.with_name(f"{target.stem}_{stamp}{target.suffix}")
    src.rename(target)
    return target


def ensure_review_checklist(file_path: str | Path, *, reset_existing: bool = True) -> bool:
    meta, body = read_markdown_parts(file_path)
    marker_exists = CHECKLIST_START in body and CHECKLIST_END in body

    if marker_exists:
        if not reset_existing:
            return False
        pattern = re.compile(
            rf"{re.escape(CHECKLIST_START)}.*?{re.escape(CHECKLIST_END)}\n?",
            flags=re.DOTALL,
        )
        body = pattern.sub(CHECKLIST_TEMPLATE, body, count=1)
    else:
        body = f"{CHECKLIST_TEMPLATE}\n{body.lstrip()}"

    write_markdown_parts(file_path, meta, body)
    return True


def run_first_review(file_path: str | Path) -> tuple[bool, list[str]]:
    meta, body = read_markdown_parts(file_path)
    reasons: list[str] = []
    # 자동 삽입 체크리스트 블록은 금지 패턴 검사에서 제외합니다.
    body_without_checklist = re.sub(
        rf"{re.escape(CHECKLIST_START)}.*?{re.escape(CHECKLIST_END)}\n?",
        "",
        body,
        flags=re.DOTALL,
    )

    for key in REVIEW_REQUIRED_FRONTMATTER_KEYS:
        if not str(meta.get(key, "")).strip():
            reasons.append(f"frontmatter `{key}` 누락")

    normalized_body = body_without_checklist.strip()
    if len(normalized_body) < REVIEW_MIN_BODY_LENGTH:
        reasons.append(f"본문 길이 부족(<{REVIEW_MIN_BODY_LENGTH})")

    for pattern in REVIEW_FORBIDDEN_PATTERNS:
        if re.search(pattern, body_without_checklist, flags=re.IGNORECASE):
            reasons.append(f"금지 패턴 발견: {pattern}")

    return (len(reasons) == 0), reasons


def manual_review_passed(file_path: str | Path) -> bool:
    meta, _ = read_markdown_parts(file_path)
    value = meta.get("manual_review_passed")
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def set_frontmatter_fields(file_path: str | Path, **fields: object) -> None:
    meta, body = read_markdown_parts(file_path)
    meta.update(fields)
    write_markdown_parts(file_path, meta, body)


def clear_manual_review_flag(file_path: str | Path) -> None:
    meta, body = read_markdown_parts(file_path)
    if "manual_review_passed" in meta:
        meta["manual_review_passed"] = False
        write_markdown_parts(file_path, meta, body)


def generate_post_id(file_path: str | Path) -> str:
    """Backward-compatible export for app layer imports."""
    return core_generate_post_id(file_path)


def list_workflow_files() -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for stage_dir in _all_known_stage_dirs():
        if not stage_dir.exists():
            continue
        for file_path in sorted(stage_dir.glob("*.md")):
            resolved = file_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(file_path)
    return files


def is_workflow_file(file_path: str | Path) -> bool:
    path_parts = _normalized_path_parts(file_path)
    notes_parts = _normalized_path_parts(NOTES_DIR)
    if path_parts[: len(notes_parts)] != notes_parts:
        return False
    return stage_from_path(file_path) is not None
