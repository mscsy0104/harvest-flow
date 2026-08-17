"""메타 DB(APP_METADATA_DB_CLIENT) 상태 점검 라우터 스크립트."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import METADATA_DB_CLIENT

SUPPORTED_CLIENTS = ("sqlite",)


def _run_checker(client_name: str, limit: int) -> None:
    if client_name == "sqlite":
        try:
            from check_sqlite_db import check_sqlite_db
        except ModuleNotFoundError:
            from scripts.check_sqlite_db import check_sqlite_db

        check_sqlite_db(limit=limit)
        return

    supported = ", ".join(SUPPORTED_CLIENTS)
    raise ValueError(
        f"지원하지 않는 --client 값입니다: {client_name!r} (지원: {supported})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="메타 DB 상태 점검 스크립트")
    parser.add_argument(
        "--client",
        default=METADATA_DB_CLIENT,
        help=f"점검할 메타 DB client 이름 (기본값: {METADATA_DB_CLIENT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="출력할 샘플 데이터 개수 (기본값: 10)",
    )
    args = parser.parse_args()

    client_name = (args.client or "").strip().lower()
    try:
        _run_checker(client_name=client_name, limit=args.limit)
    except ValueError as exc:
        print(f"❌ {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
