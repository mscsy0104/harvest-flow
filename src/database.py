"""Ollama 임베딩 및 Qdrant 검색/저장."""

from __future__ import annotations

import hashlib
import sqlite3
import time

import requests
try:
    from vector_db_client import QdrantClient
    from vector_db_client.models import Distance, VectorParams, PointStruct, PointIdsList
except ModuleNotFoundError:
    # qdrant-client 기본 모듈 경로 하위 호환
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList

from src.logger import logger
from config import (
    METADATA_DB_CLIENT,
    DB_FILE,
    VECTOR_DB_CLIENT,
    VECTOR_DB_PATH,
    VECTOR_DB_QDRANT_COLLECTION,
    LLM_EMBED_URL,
    EMBED_MODEL,
)

VECTOR_SIZE = 768
# 참조 문서로 쓸 최소 연관도 (코사인 유사도)
MIN_RETRIEVAL_SCORE = 0.70
# nomic 입력 한도 대비 안전하게 본문 앞부분만 임베딩
EMBED_MAX_CHARS = 6000
EMBED_RETRY_ATTEMPTS = 3
EMBED_RETRY_BACKOFF_SECONDS = 1.0
METADATA_DB_TABLE = "notes"
WORKFLOW_COLUMNS: tuple[tuple[str, str], ...] = (
    ("workflow_stage", "TEXT"),
    ("manual_review_passed", "INTEGER NOT NULL DEFAULT 0"),
    ("ready_for_publish_at", "REAL"),
    ("post_id", "TEXT"),
    ("last_transition_at", "REAL"),
    ("delete_requested_at", "REAL"),
    ("delete_due_at", "REAL"),
    ("delete_status", "TEXT"),
    ("delete_attempts", "INTEGER NOT NULL DEFAULT 0"),
    ("delete_last_error", "TEXT"),
    ("delete_completed_at", "REAL"),
    ("delete_cancelled_at", "REAL"),
)


def _table_has_column(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """SQLite 테이블 컬럼 존재 여부를 확인합니다."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return any(str(row[1]) == column_name for row in rows)


def _ensure_deleted_column(cursor: sqlite3.Cursor, table_name: str) -> None:
    """삭제 플래그 컬럼이 없으면 추가합니다. (하위 호환 마이그레이션)"""
    if not _table_has_column(cursor, table_name, "deleted"):
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0"
        )


def _ensure_workflow_columns(cursor: sqlite3.Cursor, table_name: str) -> None:
    """워크플로우 관련 컬럼이 없으면 추가합니다."""
    for column_name, column_def in WORKFLOW_COLUMNS:
        if _table_has_column(cursor, table_name, column_name):
            continue
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
        )


def get_sqlite_connection() -> sqlite3.Connection:
    """SQLite 메타 DB 연결을 생성합니다."""
    return sqlite3.connect(DB_FILE)


def get_metadata_db_connection() -> sqlite3.Connection:
    """선택된 메타 DB 종류에 맞춰 연결을 생성합니다."""
    if METADATA_DB_CLIENT == "sqlite":
        return get_sqlite_connection()
    raise ValueError(
        f"지원하지 않는 APP_METADATA_DB_CLIENT 값입니다: {METADATA_DB_CLIENT!r}"
    )


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """두 벡터의 코사인 유사도 (0~1 근처, 정규화된 임베딩 가정)."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = sum(x * x for x in vec_a) ** 0.5
    norm_b = sum(y * y for y in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def compute_answer_similarity(answer: str, sources: list[dict]) -> float:
    """
    답변 ↔ 참조 문서(요약/본문 발췌) 임베딩 유사도.
    근거에 얼마나 가까운 답변인지 나타냅니다.
    """
    answer = (answer or "").strip()
    if not answer or not sources:
        return 0.0

    evidence_parts: list[str] = []
    for grain in sources[:3]:
        payload = grain.get("payload") or {}
        summary = (payload.get("ai_summary_and_tags") or "").strip()
        body = (payload.get("text") or "").strip()
        evidence_parts.append(summary or body[:800])

    evidence = "\n".join(p for p in evidence_parts if p)
    if not evidence:
        return 0.0

    answer_vec = get_ollama_embedding(answer)
    evidence_vec = get_ollama_embedding(evidence)
    return cosine_similarity(answer_vec, evidence_vec)


def get_qdrant_client() -> QdrantClient:
    """Qdrant 클라이언트를 생성합니다."""
    return QdrantClient(path=VECTOR_DB_PATH, prefer_grpc=False)


def get_vector_db_client() -> QdrantClient:
    """선택된 벡터 DB 종류에 맞춰 클라이언트를 생성합니다."""
    if VECTOR_DB_CLIENT == "qdrant":
        return get_qdrant_client()
    raise ValueError(
        f"지원하지 않는 APP_VECTOR_DB_CLIENT 값입니다: {VECTOR_DB_CLIENT!r}"
    )


def get_vector_store_snapshot(limit: int = 100) -> tuple[int, list[dict]]:
    """선택된 Vector DB에서 컬렉션 건수/샘플 payload를 조회합니다."""
    client = get_vector_db_client()
    try:
        if VECTOR_DB_CLIENT == "qdrant":
            info = client.get_collection(collection_name=VECTOR_DB_QDRANT_COLLECTION)
            points, _ = client.scroll(
                collection_name=VECTOR_DB_QDRANT_COLLECTION,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            rows = [{"id": point.id, "payload": point.payload or {}} for point in points]
            return int(info.points_count or 0), rows
        raise ValueError(
            f"지원하지 않는 APP_VECTOR_DB_CLIENT 값입니다: {VECTOR_DB_CLIENT!r}"
        )
    finally:
        client.close()


def get_ollama_embedding(text: str) -> list[float]:
    """로컬 Ollama로 텍스트 임베딩 벡터를 생성합니다."""
    source_text = (text or "").strip()
    if not source_text:
        raise ValueError("임베딩 대상 텍스트가 비어 있습니다.")

    # 모델/버전 이슈로 간헐 500이 날 수 있어 재시도 + 보조 모델 fallback을 둡니다.
    models_to_try = [EMBED_MODEL]
    fallback_model = "mxbai-embed-large:latest"
    if EMBED_MODEL != fallback_model:
        models_to_try.append(fallback_model)

    max_len = min(len(source_text), EMBED_MAX_CHARS)
    length_candidates = [max_len]
    for fallback_len in (4000, 2500, 1500, 800):
        if fallback_len < max_len:
            length_candidates.append(fallback_len)

    last_error: Exception | None = None
    for clip_len in length_candidates:
        clipped = source_text[:clip_len]
        for model in models_to_try:
            for attempt in range(1, EMBED_RETRY_ATTEMPTS + 1):
                try:
                    response = requests.post(
                        LLM_EMBED_URL,
                        json={"model": model, "prompt": clipped},
                        timeout=120,
                    )
                    response.raise_for_status()
                    embedding = response.json().get("embedding")
                    if not embedding or len(embedding) != VECTOR_SIZE:
                        raise ValueError(
                            f"임베딩 차원 불일치: expected={VECTOR_SIZE}, got={len(embedding or [])}"
                        )
                    if model != EMBED_MODEL:
                        logger.warning("임베딩 fallback 모델 사용: %s", model)
                    if clip_len != max_len:
                        logger.warning("임베딩 입력 길이 축소 후 성공: %d chars", clip_len)
                    return embedding
                except Exception as exc:
                    last_error = exc
                    error_text = str(exc).lower()
                    if "input length exceeds the context length" in error_text:
                        logger.warning(
                            "임베딩 입력 길이 초과(model=%s, len=%d) → 더 짧게 재시도",
                            model,
                            clip_len,
                        )
                        break

                    is_last_attempt = attempt >= EMBED_RETRY_ATTEMPTS
                    if not is_last_attempt:
                        time.sleep(EMBED_RETRY_BACKOFF_SECONDS * attempt)
                    else:
                        logger.warning(
                            "임베딩 요청 실패(model=%s, attempt=%d/%d): %s",
                            model,
                            attempt,
                            EMBED_RETRY_ATTEMPTS,
                            str(exc),
                        )

    raise RuntimeError(f"Ollama 임베딩 요청 실패: {last_error}")


def init_infrastructure() -> None:
    """메타 DB 및 선택된 벡터 DB 인프라를 초기화합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {METADATA_DB_TABLE} "
            "("
            "filename TEXT PRIMARY KEY, "
            "last_modified REAL, "
            "status TEXT, "
            "deleted INTEGER NOT NULL DEFAULT 0, "
            "workflow_stage TEXT, "
            "manual_review_passed INTEGER NOT NULL DEFAULT 0, "
            "ready_for_publish_at REAL, "
            "post_id TEXT, "
            "last_transition_at REAL, "
            "delete_requested_at REAL, "
            "delete_due_at REAL, "
            "delete_status TEXT, "
            "delete_attempts INTEGER NOT NULL DEFAULT 0, "
            "delete_last_error TEXT, "
            "delete_completed_at REAL, "
            "delete_cancelled_at REAL"
            ")"
        )
        # 하위 호환: 과거 테이블명을 사용하던 환경도 유지합니다.
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS polished_notes "
            "("
            "filename TEXT PRIMARY KEY, "
            "last_modified REAL, "
            "status TEXT, "
            "deleted INTEGER NOT NULL DEFAULT 0, "
            "workflow_stage TEXT, "
            "manual_review_passed INTEGER NOT NULL DEFAULT 0, "
            "ready_for_publish_at REAL, "
            "post_id TEXT, "
            "last_transition_at REAL, "
            "delete_requested_at REAL, "
            "delete_due_at REAL, "
            "delete_status TEXT, "
            "delete_attempts INTEGER NOT NULL DEFAULT 0, "
            "delete_last_error TEXT, "
            "delete_completed_at REAL, "
            "delete_cancelled_at REAL"
            ")"
        )
        _ensure_deleted_column(cursor, METADATA_DB_TABLE)
        _ensure_deleted_column(cursor, "polished_notes")
        _ensure_workflow_columns(cursor, METADATA_DB_TABLE)
        _ensure_workflow_columns(cursor, "polished_notes")
        conn.commit()
    finally:
        conn.close()

    client = get_vector_db_client()
    from src.semantic_cache import ensure_cache_collection

    try:
        if not client.collection_exists(VECTOR_DB_QDRANT_COLLECTION):
            client.create_collection(
                collection_name=VECTOR_DB_QDRANT_COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
        # 선택적으로 주입 가능한 클라이언트를 재사용합니다.
        ensure_cache_collection(client)
    finally:
        client.close()


def update_metadata_db(
    filename: str,
    mtime: float,
    status: str,
    *,
    workflow_stage: str | None = None,
    manual_review_passed: bool | None = None,
    ready_for_publish_at: float | None = None,
    post_id: str | None = None,
    last_transition_at: float | None = None,
) -> None:
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        manual_review_value = (
            int(manual_review_passed)
            if manual_review_passed is not None
            else None
        )
        cursor.execute(
            f"""
            INSERT INTO {METADATA_DB_TABLE}
            (
                filename,
                last_modified,
                status,
                deleted,
                workflow_stage,
                manual_review_passed,
                ready_for_publish_at,
                post_id,
                last_transition_at
            )
            VALUES (?, ?, ?, 0, ?, COALESCE(?, 0), ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                last_modified = excluded.last_modified,
                status = excluded.status,
                deleted = 0,
                workflow_stage = COALESCE(excluded.workflow_stage, workflow_stage),
                manual_review_passed = COALESCE(excluded.manual_review_passed, manual_review_passed),
                ready_for_publish_at = COALESCE(excluded.ready_for_publish_at, ready_for_publish_at),
                post_id = COALESCE(excluded.post_id, post_id),
                last_transition_at = COALESCE(excluded.last_transition_at, last_transition_at)
            """,
            (
                filename,
                mtime,
                status,
                workflow_stage,
                manual_review_value,
                ready_for_publish_at,
                post_id,
                last_transition_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_workflow_stage(
    filename: str,
    workflow_stage: str,
    *,
    manual_review_passed: bool | None = None,
    ready_for_publish_at: float | None = None,
    post_id: str | None = None,
    transition_ts: float | None = None,
) -> None:
    """노트의 워크플로우 상태와 부가 메타를 갱신합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        set_clauses = [
            "workflow_stage = ?",
            "last_transition_at = COALESCE(?, last_transition_at)",
            "deleted = 0",
        ]
        values: list[object] = [workflow_stage, transition_ts]

        if manual_review_passed is not None:
            set_clauses.append("manual_review_passed = ?")
            values.append(int(manual_review_passed))
        if ready_for_publish_at is not None:
            set_clauses.append("ready_for_publish_at = ?")
            values.append(ready_for_publish_at)
        if post_id is not None:
            set_clauses.append("post_id = ?")
            values.append(post_id)

        values.append(filename)
        cursor.execute(
            f"UPDATE {METADATA_DB_TABLE} SET {', '.join(set_clauses)} WHERE filename = ?",
            tuple(values),
        )
        if cursor.rowcount == 0:
            update_metadata_db(
                filename,
                mtime=transition_ts or 0,
                status="",
                workflow_stage=workflow_stage,
                manual_review_passed=manual_review_passed,
                ready_for_publish_at=ready_for_publish_at,
                post_id=post_id,
                last_transition_at=transition_ts,
            )
            return
        conn.commit()
    finally:
        conn.close()


def mark_manual_review(filename: str, passed: bool, *, transition_ts: float | None = None) -> None:
    """수동 검수 통과 여부를 저장합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET manual_review_passed = ?,
                last_transition_at = COALESCE(?, last_transition_at),
                deleted = 0
            WHERE filename = ?
            """,
            (int(passed), transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def schedule_publish(filename: str, ready_for_publish_at: float, *, transition_ts: float | None = None) -> None:
    """지연 출간 시각을 저장합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET ready_for_publish_at = ?,
                last_transition_at = COALESCE(?, last_transition_at),
                deleted = 0
            WHERE filename = ?
            """,
            (ready_for_publish_at, transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def set_post_id(filename: str, post_id: str, *, transition_ts: float | None = None) -> None:
    """출간 post_id를 저장합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET post_id = ?,
                last_transition_at = COALESCE(?, last_transition_at),
                deleted = 0
            WHERE filename = ?
            """,
            (post_id, transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def get_note_metadata(filename: str) -> dict | None:
    """특정 파일명의 메타 레코드를 반환합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                filename,
                last_modified,
                status,
                deleted,
                workflow_stage,
                manual_review_passed,
                ready_for_publish_at,
                post_id,
                last_transition_at,
                delete_requested_at,
                delete_due_at,
                delete_status,
                delete_attempts,
                delete_last_error,
                delete_completed_at,
                delete_cancelled_at
            FROM {METADATA_DB_TABLE}
            WHERE filename = ?
            LIMIT 1
            """,
            (filename,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "filename": str(row[0]),
            "last_modified": float(row[1] or 0),
            "status": str(row[2] or ""),
            "deleted": int(row[3] or 0),
            "workflow_stage": row[4],
            "manual_review_passed": bool(row[5]),
            "ready_for_publish_at": float(row[6] or 0) if row[6] is not None else None,
            "post_id": row[7],
            "last_transition_at": float(row[8] or 0) if row[8] is not None else None,
            "delete_requested_at": float(row[9] or 0) if row[9] is not None else None,
            "delete_due_at": float(row[10] or 0) if row[10] is not None else None,
            "delete_status": row[11],
            "delete_attempts": int(row[12] or 0),
            "delete_last_error": row[13],
            "delete_completed_at": float(row[14] or 0) if row[14] is not None else None,
            "delete_cancelled_at": float(row[15] or 0) if row[15] is not None else None,
        }
    finally:
        conn.close()


def list_notes_by_stage(workflow_stage: str, *, include_deleted: bool = False) -> list[dict]:
    """특정 workflow_stage의 노트 목록을 조회합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        where_deleted = "" if include_deleted else "AND deleted = 0"
        cursor.execute(
            f"""
            SELECT
                filename,
                last_modified,
                status,
                deleted,
                manual_review_passed,
                ready_for_publish_at,
                post_id,
                last_transition_at,
                delete_requested_at,
                delete_due_at,
                delete_status,
                delete_attempts,
                delete_last_error,
                delete_completed_at,
                delete_cancelled_at
            FROM {METADATA_DB_TABLE}
            WHERE workflow_stage = ?
            {where_deleted}
            ORDER BY last_transition_at DESC, last_modified DESC
            """,
            (workflow_stage,),
        )
        rows = cursor.fetchall()
        return [
            {
                "filename": str(row[0]),
                "last_modified": float(row[1] or 0),
                "status": str(row[2] or ""),
                "deleted": int(row[3] or 0),
                "manual_review_passed": bool(row[4]),
                "ready_for_publish_at": float(row[5] or 0) if row[5] is not None else None,
                "post_id": row[6],
                "last_transition_at": float(row[7] or 0) if row[7] is not None else None,
                "delete_requested_at": float(row[8] or 0) if row[8] is not None else None,
                "delete_due_at": float(row[9] or 0) if row[9] is not None else None,
                "delete_status": row[10],
                "delete_attempts": int(row[11] or 0),
                "delete_last_error": row[12],
                "delete_completed_at": float(row[13] or 0) if row[13] is not None else None,
                "delete_cancelled_at": float(row[14] or 0) if row[14] is not None else None,
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_workflow_stage_counts() -> dict[str, int]:
    """삭제되지 않은 워크플로우 단계별 건수를 반환합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT workflow_stage, COUNT(*)
            FROM {METADATA_DB_TABLE}
            WHERE deleted = 0 AND workflow_stage IS NOT NULL
            GROUP BY workflow_stage
            """
        )
        rows = cursor.fetchall()
        return {str(stage): int(count) for stage, count in rows if stage}
    finally:
        conn.close()


def list_ready_to_publish(now_ts: float, *, stage_name: str = "2차검수완료") -> list[dict]:
    """지연 출간 대기 시간이 만료된 노트를 반환합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT filename, ready_for_publish_at, post_id
            FROM {METADATA_DB_TABLE}
            WHERE deleted = 0
              AND workflow_stage = ?
              AND ready_for_publish_at IS NOT NULL
              AND ready_for_publish_at <= ?
            ORDER BY ready_for_publish_at ASC
            """,
            (stage_name, now_ts),
        )
        rows = cursor.fetchall()
        return [
            {
                "filename": str(row[0]),
                "ready_for_publish_at": float(row[1] or 0),
                "post_id": row[2],
            }
            for row in rows
        ]
    finally:
        conn.close()


def schedule_delete_request(
    filename: str,
    *,
    requested_at: float,
    due_at: float,
    transition_ts: float | None = None,
) -> None:
    """지연 삭제 요청 타이머를 설정합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET delete_requested_at = ?,
                delete_due_at = ?,
                delete_status = 'requested',
                delete_attempts = 0,
                delete_last_error = NULL,
                delete_completed_at = NULL,
                delete_cancelled_at = NULL,
                last_transition_at = COALESCE(?, last_transition_at),
                deleted = 0
            WHERE filename = ?
            """,
            (requested_at, due_at, transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def cancel_delete_request(
    filename: str,
    *,
    cancelled_at: float,
    reason: str | None = None,
    transition_ts: float | None = None,
) -> None:
    """지연 삭제 요청을 취소합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET delete_status = 'cancelled',
                delete_cancelled_at = ?,
                delete_last_error = ?,
                last_transition_at = COALESCE(?, last_transition_at)
            WHERE filename = ?
            """,
            (cancelled_at, reason, transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def mark_delete_done(
    filename: str,
    *,
    completed_at: float,
    transition_ts: float | None = None,
) -> None:
    """삭제 파이프라인 성공 상태를 기록합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET delete_status = 'done',
                delete_completed_at = ?,
                delete_last_error = NULL,
                last_transition_at = COALESCE(?, last_transition_at),
                deleted = 0
            WHERE filename = ?
            """,
            (completed_at, transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def mark_delete_failed(
    filename: str,
    *,
    error_text: str,
    transition_ts: float | None = None,
) -> None:
    """삭제 파이프라인 실패 상태를 기록합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {METADATA_DB_TABLE}
            SET delete_status = 'failed',
                delete_attempts = COALESCE(delete_attempts, 0) + 1,
                delete_last_error = ?,
                last_transition_at = COALESCE(?, last_transition_at)
            WHERE filename = ?
            """,
            (error_text[:1000], transition_ts, filename),
        )
        conn.commit()
    finally:
        conn.close()


def list_ready_to_delete(now_ts: float, *, stage_name: str = "삭제요청") -> list[dict]:
    """삭제 요청 만료 시간이 지난 노트를 조회합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT filename, post_id, delete_due_at, delete_status, delete_attempts
            FROM {METADATA_DB_TABLE}
            WHERE deleted = 0
              AND workflow_stage = ?
              AND delete_due_at IS NOT NULL
              AND delete_due_at <= ?
              AND COALESCE(delete_status, 'requested') IN ('requested', 'failed')
            ORDER BY delete_due_at ASC
            """,
            (stage_name, now_ts),
        )
        rows = cursor.fetchall()
        return [
            {
                "filename": str(row[0]),
                "post_id": row[1],
                "delete_due_at": float(row[2] or 0),
                "delete_status": row[3],
                "delete_attempts": int(row[4] or 0),
            }
            for row in rows
        ]
    finally:
        conn.close()


def list_tracked_note_filenames() -> set[str]:
    """메타 DB에서 삭제되지 않은 노트 파일명 집합을 반환합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT filename FROM {METADATA_DB_TABLE} WHERE deleted = 0"
        )
        rows = cursor.fetchall()
        return {str(row[0]) for row in rows if row and row[0]}
    finally:
        conn.close()


def list_deleted_note_rows(limit: int = 1000) -> list[dict]:
    """메타 DB에서 soft delete 처리된 노트 목록을 반환합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT filename, last_modified, status
            FROM {METADATA_DB_TABLE}
            WHERE deleted = 1
            ORDER BY last_modified DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            {
                "filename": str(filename),
                "last_modified": float(last_modified or 0),
                "status": str(status or ""),
            }
            for filename, last_modified, status in rows
        ]
    finally:
        conn.close()


def delete_note_from_metadata_db(filename: str) -> None:
    """메타 DB에서 노트 1건을 soft delete(deleted=1) 처리합니다."""
    conn = get_metadata_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {METADATA_DB_TABLE} SET deleted = 1 WHERE filename = ?",
            (filename,),
        )
        # 하위 호환 테이블도 같이 정리
        cursor.execute(
            "UPDATE polished_notes SET deleted = 1 WHERE filename = ?",
            (filename,),
        )
        conn.commit()
    finally:
        conn.close()


def _point_id_from_note(note_id: str) -> int:
    return int(hashlib.sha256(note_id.encode("utf-8")).hexdigest()[:12], 16)


def delete_note_from_vector_db(note_id: str) -> None:
    """노트 ID(파일명 기준)로 벡터 포인트를 제거합니다."""
    point_id = _point_id_from_note(note_id)
    selector = PointIdsList(points=[point_id])

    client = get_vector_db_client()
    try:
        # 클라이언트 버전별 파라미터 차이를 모두 수용합니다.
        try:
            client.delete(
                collection_name=VECTOR_DB_QDRANT_COLLECTION,
                points_selector=selector,
            )
        except TypeError:
            client.delete(
                collection=VECTOR_DB_QDRANT_COLLECTION,
                points_selector=selector,
            )
    finally:
        client.close()


def save_to_vector_db(note_id: str, text: str, metadata: dict) -> None:
    """본문을 임베딩해 Qdrant에 upsert합니다."""
    try:
        vector = get_ollama_embedding(text)
    except Exception:
        logger.exception("임베딩 실패, 더미 벡터로 대체하지 않고 중단: %s", note_id)
        raise

    point_id = _point_id_from_note(note_id)
    payload = {"text": text, **metadata}

    client = get_vector_db_client()
    try:
        points = [PointStruct(id=point_id, vector=vector, payload=payload)]
        try:
            client.upsert(
                collection_name=VECTOR_DB_QDRANT_COLLECTION,
                points=points,
            )
        except TypeError:
            client.upsert(
                collection=VECTOR_DB_QDRANT_COLLECTION,
                points=points,
            )
    finally:
        client.close()


def search_knowledge_base(
    query: str,
    limit: int = 3,
    min_score: float = MIN_RETRIEVAL_SCORE,
) -> list[dict]:
    """질의 임베딩으로 유사 문서를 검색합니다. min_score 이상만 최대 limit개 반환."""
    query_vector = get_ollama_embedding(query)
    client = get_vector_db_client()
    try:
        try:
            result = client.query_points(
                collection_name=VECTOR_DB_QDRANT_COLLECTION,
                query=query_vector,
                limit=limit,
                score_threshold=min_score,
                with_payload=True,
            )
        except TypeError:
            # qdrant-client 버전별 인자명(collection_name vs collection) 하위 호환
            result = client.query_points(
                collection=VECTOR_DB_QDRANT_COLLECTION,
                query=query_vector,
                limit=limit,
                score_threshold=min_score,
                with_payload=True,
            )
        return [
            {
                "id": hit.id,
                "score": float(hit.score),
                "payload": hit.payload or {},
            }
            for hit in result.points
            if float(hit.score) >= min_score
        ][:limit]
    finally:
        client.close()


def reindex_all_embeddings(batch_limit: int = 500) -> int:
    """기존 payload.text를 다시 임베딩해 덮어씁니다. 더미 벡터 교체용."""
    client = get_vector_db_client()
    updated = 0
    try:
        points, _ = client.scroll(
            collection=VECTOR_DB_QDRANT_COLLECTION,
            limit=batch_limit,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            text = payload.get("text") or ""
            title = payload.get("title") or point.id
            if not text.strip():
                continue
            try:
                vector = get_ollama_embedding(text)
                points = [PointStruct(id=point.id, vector=vector, payload=payload)]
                try:
                    client.upsert(
                        collection_name=VECTOR_DB_QDRANT_COLLECTION,
                        points=points,
                    )
                except TypeError:
                    client.upsert(
                        collection=VECTOR_DB_QDRANT_COLLECTION,
                        points=points,
                    )
                updated += 1
                logger.info("재색인 완료: %s", title)
            except Exception:
                logger.exception("재색인 실패(스킵): %s", title)
    finally:
        client.close()
    return updated


def upload_to_github(file_name: str | None = None) -> None:
    """하위 호환 래퍼. 실제 출하는 utils.publish_content가 담당합니다."""
    from src.utils import publish_content

    if not file_name:
        logger.error("upload_to_github에는 file_name이 필요합니다.")
        return
    publish_content(file_name, client="github")
