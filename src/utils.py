import hashlib
import sqlite3
import subprocess
from pathlib import Path

from src.database import get_metadata_db_connection
from harvest_flow_core.hashing import calculate_file_hash as core_calculate_file_hash
from harvest_flow_core.ids import generate_compact_id as core_generate_compact_id
from harvest_flow_core.time_utils import (
    format_ts as core_format_ts,
    get_file_created_ts as core_get_file_created_ts,
    now_iso as core_now_iso,
    parse_iso_ts as core_parse_iso_ts,
)
from src.logger import logger
from config import METADATA_DB_CLIENT, PUBLISH_CONTENT_DIR, PUBLISH_CLIENT, GIT_BRANCH, GIT_PUSH


def _git_push_enabled() -> bool:
    if isinstance(GIT_PUSH, bool):
        return GIT_PUSH
    return str(GIT_PUSH).strip().lower() not in {"0", "false", "no", "off", ""}


def find_repo_root(start: Path | None = None) -> Path:
    """현재 위치에서 상위 방향으로 .git 이 있는 레포 루트를 찾습니다."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError("Git 저장소 루트를 찾지 못했습니다 (.git 없음).")


def push_to_github(file_name: str, *, branch: str | None = None) -> bool:
    """
    quartz_content에 기록된 파일을 add/commit/push 하여
    GitHub Actions(Quartz → Pages)를 트리거합니다.
    """
    branch = branch or GIT_BRANCH
    if not _git_push_enabled():
        logger.info("HARVEST_GIT_PUSH=0 → Git push를 건너뜁니다: %s", file_name)
        return False

    try:
        root = find_repo_root()
    except FileNotFoundError as e:
        logger.error("%s", e)
        return False

    rel_path = PUBLISH_CONTENT_DIR / file_name
    abs_path = root / rel_path
    if not abs_path.is_file():
        logger.error("출하 대상 파일이 없습니다: %s", abs_path)
        return False

    logger.info("Git 자동 출하 시작: %s", rel_path)

    def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=check,
            capture_output=True,
            text=True,
        )

    try:
        run_git("add", "--", str(rel_path))

        # staged 변경이 없으면 커밋/푸시 생략
        status = run_git("diff", "--cached", "--name-only", check=False)
        if not status.stdout.strip():
            logger.info("스테이징된 변경 없음 → 커밋 생략: %s", file_name)
            return False

        commit_message = f"📦 Harvest: {file_name} 지식 곡식 수확 배포"
        commit = run_git("commit", "-m", commit_message, check=False)
        if commit.returncode != 0:
            combined = f"{commit.stdout}\n{commit.stderr}"
            if "nothing to commit" in combined:
                logger.info("변경 없음 → 커밋 생략: %s", file_name)
                return False
            logger.error("git commit 실패: %s", commit.stderr or commit.stdout)
            return False

        run_git("push", "origin", branch)
        logger.info("Git 출하 완료 → Actions 배포가 트리거됩니다 (%s)", branch)
        return True

    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        logger.error("Git 자동 배포 실패: %s", err)
        return False
    except Exception as e:
        logger.exception("Git 스크립트 장애: %s", e)
        return False


def remove_from_github(file_name: str, *, branch: str | None = None) -> bool:
    """
    quartz_content의 파일을 git rm/commit/push 하여
    게시된 페이지에서 제거(archive/delete)합니다.
    """
    branch = branch or GIT_BRANCH
    if not _git_push_enabled():
        logger.info("HARVEST_GIT_PUSH=0 → Git 삭제 출하를 건너뜁니다: %s", file_name)
        return True

    try:
        root = find_repo_root()
    except FileNotFoundError as e:
        logger.error("%s", e)
        return False

    rel_path = PUBLISH_CONTENT_DIR / file_name
    abs_path = root / rel_path
    if not abs_path.exists():
        logger.info("삭제 출하 대상이 이미 없습니다(idempotent): %s", rel_path)
        return True

    logger.info("Git 삭제 출하 시작: %s", rel_path)

    def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=check,
            capture_output=True,
            text=True,
        )

    try:
        run_git("rm", "--", str(rel_path), check=False)

        status = run_git("diff", "--cached", "--name-only", check=False)
        if not status.stdout.strip():
            logger.info("삭제 스테이징 변경 없음 → 커밋 생략: %s", file_name)
            return True

        commit_message = f"🗑️ Harvest: {file_name} 지식 곡식 출간 철회"
        commit = run_git("commit", "-m", commit_message, check=False)
        if commit.returncode != 0:
            combined = f"{commit.stdout}\n{commit.stderr}"
            if "nothing to commit" in combined:
                logger.info("삭제 변경 없음 → 커밋 생략: %s", file_name)
                return True
            logger.error("삭제용 git commit 실패: %s", commit.stderr or commit.stdout)
            return False

        run_git("push", "origin", branch)
        logger.info("Git 삭제 출하 완료 (%s)", branch)
        return True
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        logger.error("Git 삭제 출하 실패: %s", err)
        return False
    except Exception as e:
        logger.exception("Git 삭제 스크립트 장애: %s", e)
        return False


def publish_content(file_name: str, *, client: str | None = None) -> bool:
    """
    설정된 출하 클라이언트로 콘텐츠 배포를 실행합니다.
    현재 지원: github (Quartz Pages 배포 트리거)
    """
    publish_client = (client or PUBLISH_CLIENT).strip().lower()
    if publish_client == "github":
        return push_to_github(file_name)
    raise ValueError(
        f"지원하지 않는 APP_PUBLISH_CLIENT 값입니다: {publish_client!r}"
    )


def unpublish_content(file_name: str, *, client: str | None = None) -> bool:
    """
    설정된 출하 클라이언트에서 콘텐츠 게시를 철회합니다.
    현재 지원: github (quartz_content 파일 삭제 커밋)
    """
    publish_client = (client or PUBLISH_CLIENT).strip().lower()
    if publish_client == "github":
        return remove_from_github(file_name)
    raise ValueError(
        f"지원하지 않는 APP_PUBLISH_CLIENT 값입니다: {publish_client!r}"
    )


def calculate_file_hash(file_path: str) -> str:
    """파일 본문 기준 MD5 해시를 반환합니다."""
    return core_calculate_file_hash(file_path)


def generate_compact_id(file_path: str) -> str:
    """
    문서 수정 시간과 파일명 해시를 조합한 컴팩트 고유 번호.
    예: 260712153045-4a2c
    """
    return core_generate_compact_id(file_path)


def get_file_created_ts(file_path: str) -> float:
    """가능하면 birthtime, 없으면 ctime/mtime 순으로 생성 시각(epoch)을 반환합니다."""
    return core_get_file_created_ts(file_path)


def format_ts(ts: float | None) -> str:
    return core_format_ts(ts)


def now_iso() -> str:
    return core_now_iso()


def parse_iso_ts(value: str | None) -> float:
    """정렬용: 시각 문자열 → epoch. 실패 시 0."""
    return core_parse_iso_ts(value)


def _ensure_cache_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS file_cache (
            file_path TEXT PRIMARY KEY,
            file_hash TEXT
        )
        """
    )


def is_already_cached(file_path: str, current_hash: str) -> bool:
    """동일 경로·해시가 이미 처리됐는지 조회만 합니다 (쓰기 없음)."""
    if not current_hash:
        return False

    if METADATA_DB_CLIENT != "sqlite":
        logger.warning("META DB client '%s'는 file_cache 조회를 지원하지 않습니다.", METADATA_DB_CLIENT)
        return False

    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        _ensure_cache_table(cursor)
        cursor.execute(
            "SELECT file_hash FROM file_cache WHERE file_path = ?",
            (file_path,),
        )
        row = cursor.fetchone()
        return bool(row and row[0] == current_hash)
    finally:
        conn.close()


def update_file_cache(file_path: str, file_hash: str) -> None:
    """파이프라인 성공 후에만 해시를 기록합니다."""
    if not file_hash:
        return

    if METADATA_DB_CLIENT != "sqlite":
        logger.warning("META DB client '%s'는 file_cache 저장을 지원하지 않습니다.", METADATA_DB_CLIENT)
        return

    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        _ensure_cache_table(cursor)
        cursor.execute(
            "INSERT OR REPLACE INTO file_cache (file_path, file_hash) VALUES (?, ?)",
            (file_path, file_hash),
        )
        conn.commit()
    finally:
        conn.close()


def list_cached_file_paths() -> set[str]:
    """file_cache에 저장된 파일 경로 목록을 반환합니다."""
    if METADATA_DB_CLIENT != "sqlite":
        logger.warning("META DB client '%s'는 file_cache 조회를 지원하지 않습니다.", METADATA_DB_CLIENT)
        return set()

    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        _ensure_cache_table(cursor)
        cursor.execute("SELECT file_path FROM file_cache")
        rows = cursor.fetchall()
        return {str(row[0]) for row in rows if row and row[0]}
    finally:
        conn.close()


def delete_file_cache_entry(file_path: str) -> None:
    """file_cache에서 특정 경로의 캐시를 제거합니다."""
    if METADATA_DB_CLIENT != "sqlite":
        logger.warning("META DB client '%s'는 file_cache 삭제를 지원하지 않습니다.", METADATA_DB_CLIENT)
        return

    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        _ensure_cache_table(cursor)
        cursor.execute(
            "DELETE FROM file_cache WHERE file_path = ?",
            (file_path,),
        )
        conn.commit()
    finally:
        conn.close()
