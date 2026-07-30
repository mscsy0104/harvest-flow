"""로컬 Ollama 속도/모델 공통 설정."""

from config.env import get_env, get_int_env

LLM_GENERATE_URL = get_env(
    "OLLAMA_GENERATE_URL",
    "http://localhost:11434/api/generate",
)

# 요약·태그는 가벼운 모델, RAG도 속도 우선 (품질 필요 시 교체)
PIPELINE_MODEL = get_env("OLLAMA_PIPELINE_MODEL", "gemma2:2b")
RAG_MODEL = get_env("OLLAMA_RAG_MODEL", "gemma2:2b")

KEEP_ALIVE = get_env("OLLAMA_KEEP_ALIVE", "30m")
PIPELINE_NUM_PREDICT = get_int_env("OLLAMA_PIPELINE_NUM_PREDICT", 160)
RAG_NUM_PREDICT = get_int_env("OLLAMA_RAG_NUM_PREDICT", 256)

# 컨텍스트 축소 (토큰↓ = 지연↓)
PIPELINE_BODY_MAX_CHARS = get_int_env("OLLAMA_PIPELINE_BODY_MAX_CHARS", 2500)
RAG_BODY_MAX_CHARS = get_int_env("OLLAMA_RAG_BODY_MAX_CHARS", 800)
