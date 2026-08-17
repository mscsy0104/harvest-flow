'''
DB: SQLite
Vector DB: Qdrant
Note App: Obsidian Vault
Publishing SSG: Quartz

확장성을 고려해서 개념 용어(DB, BLOG, ...)로 쓰고 
특정 도구 종속 개념은 자세하게 작성
'''
from pathlib import Path

from config.env import get_bool_env, get_env, get_float_env, get_int_env

# 1. [경로 상수] 프로젝트 루트 경로 설정 (config/ 폴더의 부모 폴더)
BASE_DIR = Path(__file__).resolve().parent.parent


def _require_min_int(name: str, value: int, minimum: int = 0) -> int:
    if value < minimum:
        raise RuntimeError(
            f"{name} 값은 {minimum} 이상이어야 합니다. 현재 값: {value}"
        )
    return value


def _require_float_range(name: str, value: float, minimum: float, maximum: float) -> float:
    if value < minimum or value > maximum:
        raise RuntimeError(
            f"{name} 값은 {minimum}~{maximum} 범위여야 합니다. 현재 값: {value}"
        )
    return value


# 2. [환경 변수 및 기본값 설정] 외부 설정에 따라 바뀔 수 있는 값들
# 데이터베이스 파일명 및 URL
METADATA_DB_CLIENT = get_env("APP_METADATA_DB_CLIENT", "sqlite").strip().lower()
METADATA_DB = get_env("APP_METADATA_DB", "pipeline_metadata.db")
METADATA_DB_URL = f"sqlite:///{BASE_DIR / METADATA_DB}"

# Qdrant 로컬 저장소 경로 및 컬렉션 이름
VECTOR_DB_CLIENT = get_env("APP_VECTOR_DB_CLIENT", "qdrant").strip().lower()
VECTOR_DB_DIR = get_env("APP_VECTOR_DB_DIR", "qdrant_local")
VECTOR_DB_PATH = BASE_DIR / VECTOR_DB_DIR
VECTOR_DB_QDRANT_COLLECTION = get_env("APP_QDRANT_COLLECTION", "harvest_notes")

# 로그 및 콘텐츠 폴더 경로
LOG_STEM = get_env("APP_LOG_STEM", "logs")
LOG_LEVEL = get_env("APP_LOG_LEVEL", "INFO").strip().upper()
PUBLISH_CONTENT_STEM = get_env(
    "APP_PUBLISH_CONTENT_STEM",
    get_env("APP_BLOG_CONTENT_STEM", "publish_content"),
)
NOTES_APP_NAME=get_env("NOTES_APP_NAME", "markdown-notes")
NOTES_STEM = get_env("APP_VAULT_STEM", "notes_vault")

LOG_DIR = BASE_DIR / LOG_STEM
PUBLISH_CONTENT_DIR = BASE_DIR / PUBLISH_CONTENT_STEM
NOTES_DIR = BASE_DIR / NOTES_STEM

# 외부 API 및 모델 URL
LLM_EMBED_URL = get_env("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
EMBED_MODEL = get_env("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# Git 관련 설정 (정수/불리언 값은 안정성을 위해 변환 처리 권장)
PUBLISH_CLIENT = get_env("APP_PUBLISH_CLIENT", "github").strip().lower()
GIT_BRANCH = get_env("GIT_BRANCH", "main")
GIT_PUSH = get_bool_env("GIT_PUSH", False)
STARTUP_SYNC = get_bool_env("APP_STARTUP_SYNC", True)
PUBLISH_DELAY_MINUTES = _require_min_int(
    "APP_PUBLISH_DELAY_MINUTES",
    get_int_env("APP_PUBLISH_DELAY_MINUTES", 1),
    minimum=0,
)
DELETE_DELAY_MINUTES = _require_min_int(
    "APP_DELETE_DELAY_MINUTES",
    get_int_env("APP_DELETE_DELAY_MINUTES", 60),
    minimum=0,
)
CACHE_SIMILARITY_THRESHOLD = _require_float_range(
    "APP_CACHE_SIM_THRESHOLD",
    get_float_env("APP_CACHE_SIM_THRESHOLD", 0.93),
    minimum=0.0,
    maximum=1.0,
)
CACHE_RECENT_LIMIT = _require_min_int(
    "APP_CACHE_RECENT_LIMIT",
    get_int_env("APP_CACHE_RECENT_LIMIT", 20),
    minimum=1,
)

# 워크플로우 폴더명
WORKFLOW_DRAFT_DIR_NAME = get_env("APP_WORKFLOW_DRAFT_DIR", "1_초안")
WORKFLOW_REVIEW_REQUEST_DIR_NAME = get_env("APP_WORKFLOW_REVIEW_REQUEST_DIR", "2_검수요청")
WORKFLOW_PUBLISH_WAIT_DIR_NAME = get_env("APP_WORKFLOW_PUBLISH_WAIT_DIR", "3_출간대기")
WORKFLOW_NEEDS_FIX_DIR_NAME = get_env("APP_WORKFLOW_NEEDS_FIX_DIR", "4_수정필요")
WORKFLOW_SECOND_REVIEW_DONE_DIR_NAME = get_env("APP_WORKFLOW_SECOND_REVIEW_DONE_DIR", "5_2차검수완료")
WORKFLOW_PUBLISHED_DIR_NAME = get_env("APP_WORKFLOW_PUBLISHED_DIR", "6_출간완료")
WORKFLOW_REVISE_WAIT_DIR_NAME = get_env("APP_WORKFLOW_REVISE_WAIT_DIR", "7_수정대기")
WORKFLOW_DELETE_REQUEST_DIR_NAME = get_env("APP_WORKFLOW_DELETE_REQUEST_DIR", "8_삭제요청")
WORKFLOW_TRASH_DIR_NAME = get_env("APP_WORKFLOW_TRASH_DIR", "9_휴지통")

# 워크플로우 폴더 경로
WORKFLOW_DRAFT_DIR = NOTES_DIR / WORKFLOW_DRAFT_DIR_NAME
WORKFLOW_REVIEW_REQUEST_DIR = NOTES_DIR / WORKFLOW_REVIEW_REQUEST_DIR_NAME
WORKFLOW_PUBLISH_WAIT_DIR = NOTES_DIR / WORKFLOW_PUBLISH_WAIT_DIR_NAME
WORKFLOW_NEEDS_FIX_DIR = NOTES_DIR / WORKFLOW_NEEDS_FIX_DIR_NAME
WORKFLOW_SECOND_REVIEW_DONE_DIR = NOTES_DIR / WORKFLOW_SECOND_REVIEW_DONE_DIR_NAME
WORKFLOW_PUBLISHED_DIR = NOTES_DIR / WORKFLOW_PUBLISHED_DIR_NAME
WORKFLOW_REVISE_WAIT_DIR = NOTES_DIR / WORKFLOW_REVISE_WAIT_DIR_NAME
WORKFLOW_DELETE_REQUEST_DIR = NOTES_DIR / WORKFLOW_DELETE_REQUEST_DIR_NAME
WORKFLOW_TRASH_DIR = NOTES_DIR / WORKFLOW_TRASH_DIR_NAME

# 하위 호환 별칭
QDRANT_PATH = VECTOR_DB_PATH
QDRANT_COLLECTION_NAME = VECTOR_DB_QDRANT_COLLECTION
COLLECTION_NAME = VECTOR_DB_QDRANT_COLLECTION


def _safe_mkdir(path: Path) -> None:
    """권한/환경 이슈가 있어도 import 실패를 막기 위해 안전 생성."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # 외부 경로 권한 이슈는 런타임에서 별도로 안내하고 import는 유지합니다.
        pass


def ensure_runtime_directories() -> None:
    """앱 엔트리에서 명시적으로 호출하는 디렉터리 초기화."""
    runtime_dirs = [
        NOTES_DIR,
        WORKFLOW_DRAFT_DIR,
        WORKFLOW_REVIEW_REQUEST_DIR,
        WORKFLOW_PUBLISH_WAIT_DIR,
        WORKFLOW_NEEDS_FIX_DIR,
        WORKFLOW_SECOND_REVIEW_DONE_DIR,
        WORKFLOW_PUBLISHED_DIR,
        WORKFLOW_REVISE_WAIT_DIR,
        WORKFLOW_DELETE_REQUEST_DIR,
        WORKFLOW_TRASH_DIR,
        LOG_DIR,
        PUBLISH_CONTENT_DIR,
    ]
    if VECTOR_DB_CLIENT == "qdrant":
        runtime_dirs.insert(0, VECTOR_DB_PATH)

    for directory in runtime_dirs:
        _safe_mkdir(directory)