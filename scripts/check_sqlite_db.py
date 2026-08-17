"""SQLite 메타 DB 적재 상태를 점검하는 전용 스크립트."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import METADATA_DB
from harvest_flow.database import get_sqlite_connection

TARGET_TABLES = ("notes", "polished_notes", "file_cache")


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _print_table_count(cursor, table_name: str) -> None:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = int((cursor.fetchone() or [0])[0])
    print(f"- {table_name}: {count} rows")


def _print_notes_preview(cursor, table_name: str, limit: int) -> None:
    cursor.execute(
        f"""
        SELECT filename, last_modified, status
        FROM {table_name}
        ORDER BY last_modified DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    if not rows:
        print(f"\n🔍 [{table_name}] 샘플 데이터 없음")
        return

    print(f"\n🔍 [{table_name}] 최신 {len(rows)}건")
    for filename, last_modified, status in rows:
        print(f"- {filename} | mtime={last_modified} | status={status}")


def _print_file_cache_preview(cursor, limit: int) -> None:
    cursor.execute(
        """
        SELECT file_path, file_hash
        FROM file_cache
        ORDER BY file_path ASC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    if not rows:
        print("\n🔍 [file_cache] 샘플 데이터 없음")
        return

    print(f"\n🔍 [file_cache] 샘플 {len(rows)}건")
    for file_path, file_hash in rows:
        preview_hash = (file_hash or "")[:12]
        print(f"- {file_path} | hash={preview_hash}...")


def check_sqlite_db(limit: int = 10) -> None:
    """메타 SQLite DB의 테이블 건수와 샘플 데이터를 출력합니다."""
    conn = get_sqlite_connection()
    try:
        cursor = conn.cursor()
        print(f"📊 SQLite 메타 DB 파일: {METADATA_DB}")
        print("📚 테이블 건수")
        for table_name in TARGET_TABLES:
            if _table_exists(cursor, table_name):
                _print_table_count(cursor, table_name)
            else:
                print(f"- {table_name}: (table not found)")

        if _table_exists(cursor, "notes"):
            _print_notes_preview(cursor, "notes", limit)
        elif _table_exists(cursor, "polished_notes"):
            _print_notes_preview(cursor, "polished_notes", limit)

        if _table_exists(cursor, "file_cache"):
            _print_file_cache_preview(cursor, limit)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="SQLite 메타 DB 상태 점검 스크립트")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="출력할 샘플 데이터 개수 (기본값: 10)",
    )
    args = parser.parse_args()
    check_sqlite_db(limit=args.limit)


if __name__ == "__main__":
    main()
