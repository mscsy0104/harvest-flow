"""로컬 LLM 기반 RAG 답변 생성 (짧은 컨텍스트 + 스트리밍)."""

from __future__ import annotations

import json
from collections.abc import Iterator

import requests

from config import (
    LLM_GENERATE_URL,
    RAG_MODEL,
    RAG_NUM_PREDICT,
    RAG_BODY_MAX_CHARS,
    KEEP_ALIVE,
)
from src.logger import logger

TEMPERATURE = 0.2

def _clip(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


def _build_context(retrieved_docs: list[dict]) -> str:
    """요약 위주 + 본문 앞부분만 넣어 프롬프트를 가볍게 유지합니다."""
    chunks: list[str] = []
    for idx, doc in enumerate(retrieved_docs, start=1):
        payload = doc.get("payload") or {}
        title = payload.get("title") or "(제목 없음)"
        summary = payload.get("ai_summary_and_tags") or ""
        body = _clip(
            payload.get("text") or payload.get("content") or "",
            RAG_BODY_MAX_CHARS,
        )
        chunks.append(
            f"[참조 {idx}] 제목: {title}\n"
            f"요약:\n{summary}\n"
            f"본문 발췌:\n{body}\n"
        )
    return "\n".join(chunks)


def _build_prompt(query: str, retrieved_docs: list[dict]) -> str:
    context_str = _build_context(retrieved_docs)
    return (
        "제공된 [지식 곳간 참조 문서]의 내용에만 기반하여 질문에 답변하세요.\n"
        "답변은 3~6문장으로 간결하게 작성하세요.\n"
        "창고 문서에 없는 내용이라면 억지로 지어내지 말고 "
        "'창고에 관련 지식이 비축되어 있지 않습니다'라고 답하세요.\n\n"
        f"[지식 곳간 참조 문서]\n{context_str}\n"
        f"[사용자 질문]\n{query}\n\n답변:"
    )


def iter_rag_answer(query: str, retrieved_docs: list[dict]) -> Iterator[str]:
    """토큰(청크) 단위로 답변을 스트리밍합니다."""
    prompt = _build_prompt(query, retrieved_docs)
    logger.info("RAG 스트리밍 시작 (model=%s, 질의: %s)", RAG_MODEL, query)

    try:
        with requests.post(
            LLM_GENERATE_URL,
            json={
                "model": RAG_MODEL,
                "prompt": prompt,
                "stream": True,
                "keep_alive": KEEP_ALIVE,
                "options": {
                    "temperature": TEMPERATURE,
                    "num_predict": RAG_NUM_PREDICT,
                },
            },
            stream=True,
            timeout=180,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                chunk = json.loads(line)
                piece = chunk.get("response") or ""
                if piece:
                    yield piece
                if chunk.get("done"):
                    break
        logger.info("RAG 스트리밍 완료")
    except Exception as e:
        logger.exception("RAG 추론 실패: %s", e)
        yield "로컬 AI 엔진이 답변을 생성하는 데 실패했습니다."


def generate_rag_answer(query: str, retrieved_docs: list[dict]) -> str:
    """비스트리밍 편의 래퍼."""
    return "".join(iter_rag_answer(query, retrieved_docs)).strip() or "답변이 비어 있습니다."
