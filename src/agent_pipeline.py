"""출간 파이프라인용 요약·태그 생성 (빠른 SLM)."""

from __future__ import annotations

import requests

from config import (
    LLM_GENERATE_URL,
    PIPELINE_MODEL,
    PIPELINE_NUM_PREDICT,
    PIPELINE_BODY_MAX_CHARS,
    KEEP_ALIVE,
)
from src.logger import logger


def _clip(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n…(이하 생략)"


def generate_ai_metadata(body_text: str) -> str:
    """로컬 LLM으로 본문 요약 및 키워드 태그를 추출합니다."""
    body = _clip(body_text, PIPELINE_BODY_MAX_CHARS)
    prompt = (
        "당신은 테크 블로그 전문 편집자입니다. 다음 본문을 읽고 두 가지만 수행하세요.\n"
        "1. 본문을 딱 2줄로 요약 (각 줄 앞에 '- ').\n"
        "2. 핵심 키워드 태그 3개 (예: #데이터 #생산성).\n"
        "군더더기 설명 없이 아래 포맷만 출력하세요.\n\n"
        f"[본문]\n{body}\n\n"
        "[출력 포맷]\n"
        "요약:\n"
        "- ...\n"
        "- ...\n"
        "태그:\n"
        "#태그1 #태그2 #태그3\n"
    )

    logger.info("파이프라인 LLM 요약 시작 (model=%s)", PIPELINE_MODEL)
    try:
        response = requests.post(
            LLM_GENERATE_URL,
            json={
                "model": PIPELINE_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": KEEP_ALIVE,
                "options": {
                    "temperature": 0.2,
                    "num_predict": PIPELINE_NUM_PREDICT,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        answer = (response.json().get("response") or "").strip()
        logger.info("파이프라인 LLM 요약 완료")
        return answer or "요약 결과가 비어 있습니다."
    except Exception as e:
        logger.exception("파이프라인 LLM 실패: %s", e)
        return f"AI 정제 실패 (Ollama 미구동 또는 에러): {e}"
