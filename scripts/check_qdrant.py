"""Qdrant 적재 상태를 점검하는 전용 스크립트."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import VECTOR_DB_QDRANT_COLLECTION
from src.database import get_qdrant_client


def check_qdrant(limit: int = 10) -> None:
    """Qdrant 컬렉션 건수와 샘플 payload를 출력합니다."""
    client = get_qdrant_client()
    try:
        info = client.get_collection(collection_name=VECTOR_DB_QDRANT_COLLECTION)
        print(f"📊 현재 Qdrant 저장 노트 수: {info.points_count}개")

        scroll_result, _ = client.scroll(
            collection_name=VECTOR_DB_QDRANT_COLLECTION,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        print("\n🔍 [Qdrant 적재 데이터 목록]")
        for point in scroll_result:
            payload = point.payload or {}
            print(f"- ID: {point.id}")
            print(f"  제목: {payload.get('title')} | 상태: {payload.get('status')}")
            print(f"  🤖 AI 분석 데이터:\n{payload.get('ai_summary_and_tags')}")
            print("-" * 40)
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Qdrant 상태 점검 스크립트")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="출력할 샘플 데이터 개수 (기본값: 10)",
    )
    args = parser.parse_args()
    check_qdrant(limit=args.limit)


if __name__ == "__main__":
    main()