"""질문 의도 기반 시맨틱 캐시 (Qdrant llm_cache)."""

from __future__ import annotations

import hashlib

try:
    from vector_db_client import QdrantClient
    from vector_db_client.models import Distance, PointStruct, VectorParams
except ModuleNotFoundError:
    # qdrant-client 기본 모듈 경로 하위 호환
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

from src.database import (
    VECTOR_SIZE,
    get_ollama_embedding,
    get_vector_db_client,
)
from src.logger import logger
from src.utils import now_iso

CACHE_COLLECTION = "llm_cache"
# 코사인 유사도 임계값 (조정 가능)
SIMILARITY_THRESHOLD = 0.93


def ensure_cache_collection(client: QdrantClient | None = None) -> None:
    """llm_cache 컬렉션이 없으면 생성합니다."""
    owns_client = client is None
    if client is None:
        client = get_vector_db_client()
    try:
        if not client.collection_exists(CACHE_COLLECTION):
            client.create_collection(
                collection_name=CACHE_COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("시맨틱 캐시 컬렉션 생성: %s", CACHE_COLLECTION)
    finally:
        if owns_client:
            client.close()


def _cache_point_id(query_text: str) -> int:
    """동일 문자열 질문은 같은 point로 upsert되도록 안정적 ID를 만듭니다."""
    digest = hashlib.md5(query_text.strip().encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def get_cached_answer(query_text: str) -> dict | None:
    """
    과거 질문 벡터와 의미 유사도를 비교합니다.
    임계값 이상이면 answer / past_query / score / sources 등을 담은 dict를 반환합니다.
    """
    query = (query_text or "").strip()
    if not query:
        return None

    ensure_cache_collection()
    query_vector = get_ollama_embedding(query)
    client = get_vector_db_client()
    try:
        try:
            result = client.query_points(
                collection_name=CACHE_COLLECTION,
                query=query_vector,
                limit=1,
                with_payload=True,
            )
        except TypeError:
            # qdrant-client 버전별 인자명(collection_name vs collection) 하위 호환
            result = client.query_points(
                collection=CACHE_COLLECTION,
                query=query_vector,
                limit=1,
                with_payload=True,
            )
        if not result.points:
            return None

        hit = result.points[0]
        score = float(hit.score)
        if score < SIMILARITY_THRESHOLD:
            return None

        payload = hit.payload or {}
        logger.info(
            "시맨틱 캐시 적중 (%.1f%%) past='%s' current='%s'",
            score * 100,
            payload.get("past_query"),
            query,
        )
        return {
            "answer": payload.get("cached_answer") or "",
            "past_query": payload.get("past_query") or "",
            "score": score,  # 현재 질문 ↔ 과거 질문
            "doc_similarity": float(payload.get("doc_similarity") or 0),
            "answer_similarity": float(payload.get("answer_similarity") or 0),
            "cached_at": payload.get("cached_at"),
            "sources": payload.get("sources") or [],
        }
    finally:
        client.close()


def save_to_cache(
    query_text: str,
    answer_text: str,
    sources: list[dict] | None = None,
    doc_similarity: float | None = None,
    answer_similarity: float | None = None,
) -> None:
    """새 질문·답변·참조 문서 메타를 시맨틱 캐시에 저장합니다."""
    query = (query_text or "").strip()
    answer = (answer_text or "").strip()
    if not query or not answer:
        return

    ensure_cache_collection()
    query_vector = get_ollama_embedding(query)
    point_id = _cache_point_id(query)
    cached_at = now_iso()

    # UI/직렬화용으로 필요한 필드만 압축 저장
    compact_sources = []
    for grain in sources or []:
        payload = grain.get("payload") or {}
        compact_sources.append(
            {
                "id": grain.get("id"),
                "score": float(grain.get("score") or 0),
                "payload": {
                    "title": payload.get("title"),
                    "compact_id": payload.get("compact_id"),
                    "text": payload.get("text") or "",
                    "ai_summary_and_tags": payload.get("ai_summary_and_tags") or "",
                },
            }
        )

    if doc_similarity is None and compact_sources:
        doc_similarity = float(compact_sources[0].get("score") or 0)
    if answer_similarity is None and compact_sources:
        from src.database import compute_answer_similarity

        answer_similarity = compute_answer_similarity(answer, compact_sources)

    client = get_vector_db_client()
    try:
        points = [
            PointStruct(
                id=point_id,
                vector=query_vector,
                payload={
                    "past_query": query,
                    "cached_answer": answer,
                    "cached_at": cached_at,
                    "sources": compact_sources,
                    "doc_similarity": float(doc_similarity or 0),
                    "answer_similarity": float(answer_similarity or 0),
                },
            )
        ]
        try:
            client.upsert(
                collection_name=CACHE_COLLECTION,
                points=points,
            )
        except TypeError:
            client.upsert(
                collection=CACHE_COLLECTION,
                points=points,
            )
        logger.info(
            "시맨틱 캐시 저장: %s (참조 %d건, 답변유사도 %.1f%%)",
            query,
            len(compact_sources),
            float(answer_similarity or 0) * 100,
        )
    finally:
        client.close()


def list_recent_cached_queries(limit: int = 20) -> list[dict]:
    """대시보드용: 최근 캐시된 질의 목록 (재활용·히스토리)."""
    ensure_cache_collection()
    client = get_vector_db_client()
    try:
        points, _ = client.scroll(
            collection_name=CACHE_COLLECTION,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        rows = []
        for point in points:
            payload = point.payload or {}
            rows.append(
                {
                    "id": point.id,
                    "past_query": payload.get("past_query") or "",
                    "cached_at": payload.get("cached_at") or "",
                    "answer_preview": (payload.get("cached_answer") or "")[:120],
                }
            )
        rows.sort(key=lambda r: r.get("cached_at") or "", reverse=True)
        return rows
    finally:
        client.close()
