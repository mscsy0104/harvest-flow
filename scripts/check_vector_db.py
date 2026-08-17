"""
선택된 벡터 DB(APP_VECTOR_DB_CLIENT) 적재 상태 확인 스크립트.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import VECTOR_DB_CLIENT


SUPPORTED_CLIENTS = ("qdrant",)


def _run_checker(client_name: str, limit: int) -> None:
    if client_name == "qdrant":
        # python scripts/check_vector_db.py 형태 실행을 고려한 import
        try:
            from check_qdrant import check_qdrant
        except ModuleNotFoundError:
            from scripts.check_qdrant import check_qdrant

        check_qdrant(limit=limit)
        return

    supported = ", ".join(SUPPORTED_CLIENTS)
    raise ValueError(
        f"지원하지 않는 --client 값입니다: {client_name!r} (지원: {supported})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Vector DB 상태 점검 스크립트")
    parser.add_argument(
        "--client",
        default=VECTOR_DB_CLIENT,
        help=f"점검할 벡터 DB client 이름 (기본값: {VECTOR_DB_CLIENT})",
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
