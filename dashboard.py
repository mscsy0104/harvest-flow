import streamlit as st
from pathlib import Path
from math import ceil
from datetime import datetime, timedelta

from src.logger import read_recent_logs
from src.utils import (
    generate_compact_id,
    get_file_created_ts,
    format_ts,
    parse_iso_ts,
)
from src.database import (
    search_knowledge_base,
    reindex_all_embeddings,
    MIN_RETRIEVAL_SCORE,
    compute_answer_similarity,
    get_vector_store_snapshot,
    list_deleted_note_rows,
    get_workflow_stage_counts,
)
from src.agent_rag import iter_rag_answer
from config import (
    RAG_MODEL,
    PIPELINE_MODEL,
    NOTES_APP_NAME,
    NOTES_DIR,
    PUBLISH_CONTENT_DIR,
    PUBLISH_CLIENT,
    VECTOR_DB_CLIENT,
)
from src.semantic_cache import (
    get_cached_answer,
    save_to_cache,
    list_recent_cached_queries,
)
from src.workflow import (
    STAGE_DRAFT,
    STAGE_REVIEW_REQUEST,
    STAGE_PUBLISH_WAIT,
    STAGE_NEEDS_FIX,
    STAGE_SECOND_REVIEW_DONE,
    STAGE_PUBLISHED,
    STAGE_REVISE_WAIT,
    STAGE_DELETE_REQUEST,
    STAGE_TRASH,
    WORKFLOW_STAGE_DIRS,
    LEGACY_WORKFLOW_STAGE_DIRS,
)

# 1. 페이지 기본 설정 및 스타일 정의 (따뜻한 대농장 감성 테마)
st.set_page_config(page_title="HarvestFlow Dashboard", layout="wide")

# CSS를 활용해 게시판 리스트 디자인을 대농장/곡식 창고 톤으로 튜닝
st.markdown("""
    <style>
    :root {
        --hf-text-main: #1f2f1b;
        --hf-text-sub: #38533a;
        --hf-btn-bg: #eef8e9;
        --hf-btn-bg-hover: #e4f3df;
        --hf-btn-text: #1e3a1f;
        --hf-btn-border: #6da05d;
        --hf-btn-disabled-bg: #dde6da;
        --hf-btn-disabled-text: #6f7f70;
        --hf-app-bg:
            radial-gradient(circle at 15% 12%, rgba(255,255,255,0.80) 0 7%, transparent 8%),
            radial-gradient(circle at 86% 10%, rgba(255,255,255,0.72) 0 8%, transparent 9%),
            linear-gradient(180deg, #7fd8ff 0%, #b5ecff 32%, #daf9f1 55%, #f7fbf3 100%);
        --hf-sidebar-bg: linear-gradient(180deg, rgba(245,253,244,0.95), rgba(238,248,232,0.9));
        --hf-contrib-0: #eef3ec;
        --hf-contrib-1: #b8e2b4;
        --hf-contrib-2: #77c56f;
        --hf-contrib-3: #3ea44a;
        --hf-contrib-4: #2e7d32;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --hf-text-main: #1f2f1b;
            --hf-text-sub: #38533a;
            --hf-btn-bg: #eef8e9;
            --hf-btn-bg-hover: #e4f3df;
            --hf-btn-text: #1e3a1f;
            --hf-btn-border: #6da05d;
            --hf-btn-disabled-bg: #dde6da;
            --hf-btn-disabled-text: #6f7f70;
            --hf-app-bg:
                radial-gradient(circle at 15% 12%, rgba(255,255,255,0.80) 0 7%, transparent 8%),
                radial-gradient(circle at 86% 10%, rgba(255,255,255,0.72) 0 8%, transparent 9%),
                linear-gradient(180deg, #7fd8ff 0%, #b5ecff 32%, #daf9f1 55%, #f7fbf3 100%);
            --hf-sidebar-bg: linear-gradient(180deg, rgba(245,253,244,0.95), rgba(238,248,232,0.9));
            --hf-contrib-0: #eef3ec;
            --hf-contrib-1: #b8e2b4;
            --hf-contrib-2: #77c56f;
            --hf-contrib-3: #3ea44a;
            --hf-contrib-4: #2e7d32;
        }
    }
    /* 메인 화면 상단 여백 조정 */
    .reportview-container .main .block-container { padding-top: 1.4rem; }
    [data-testid="stAppViewContainer"] {
        background: var(--hf-app-bg);
    }
    [data-testid="stSidebar"] {
        background: var(--hf-sidebar-bg);
        border-right: 1px solid rgba(83, 109, 44, 0.18);
    }
    /* 브라우저 다크모드 강제 시 텍스트가 흰색으로 뜨는 문제 방지 */
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3,
    [data-testid="stAppViewContainer"] h4,
    [data-testid="stAppViewContainer"] h5,
    [data-testid="stAppViewContainer"] h6,
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: var(--hf-text-main) !important;
    }
    [data-testid="stAppViewContainer"] .stCaption {
        color: var(--hf-text-sub) !important;
    }
    .farm-hero {
        background: linear-gradient(135deg, rgba(60, 159, 95, 0.92), rgba(109, 183, 84, 0.9));
        border: 1px solid rgba(46, 110, 44, 0.28);
        border-radius: 18px;
        padding: 18px 20px 16px 20px;
        color: #f7fff8;
        box-shadow: 0 8px 22px rgba(39, 76, 35, 0.18);
        margin-bottom: 14px;
    }
    .farm-hero-title {
        font-size: 1.45rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .farm-hero-subtitle {
        font-size: 0.94rem;
        opacity: 0.95;
        margin-bottom: 10px;
    }
    .farm-chip-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .farm-chip {
        background: rgba(255, 255, 255, 0.17);
        border: 1px solid rgba(255, 255, 255, 0.35);
        color: #f6fff0;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
    }
    .publish-info-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(90, 110, 75, 0.35);
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 10px rgba(45, 58, 34, 0.08);
    }
    .publish-info-row {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin: 4px 0;
        line-height: 1.35;
    }
    .publish-info-key {
        min-width: 96px;
        font-weight: 700;
        color: var(--hf-text-sub);
    }
    .publish-info-value {
        color: var(--hf-text-main);
        word-break: break-word;
    }
    .workflow-stage-card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(90, 110, 75, 0.35);
        border-radius: 12px;
        padding: 10px 12px;
        box-shadow: 0 2px 10px rgba(45, 58, 34, 0.08);
        margin-top: 4px;
        margin-bottom: 8px;
    }
    .workflow-stage-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px 10px;
    }
    .workflow-stage-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed rgba(90, 110, 75, 0.25);
        padding-bottom: 2px;
        font-size: 0.82rem;
        color: var(--hf-text-main);
    }
    .workflow-stage-item:last-child {
        border-bottom: none;
    }
    .workflow-stage-key {
        color: var(--hf-text-sub);
        font-weight: 600;
    }
    .workflow-stage-val {
        font-weight: 700;
    }
    @media (prefers-color-scheme: dark) {
        .publish-info-card {
            background: rgba(245, 251, 243, 0.95);
            border: 1px solid rgba(101, 126, 83, 0.5);
        }
        .workflow-stage-card {
            background: rgba(245, 251, 243, 0.95);
            border: 1px solid rgba(101, 126, 83, 0.5);
        }
    }
    .farm-hero * {
        color: #f7fff8 !important;
    }
    [data-testid="stButton"] button,
    .stButton button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
        border-radius: 10px !important;
        border: 1px solid var(--hf-btn-border) !important;
        background-color: #e6f4e0 !important;
        color: var(--hf-btn-text) !important;
        box-shadow: 0 2px 6px rgba(68, 102, 56, 0.15) !important;
        transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.08s ease;
    }
    [data-testid="stButton"] button p,
    .stButton button p {
        width: 100% !important;
        margin: 0 !important;
        text-align: center !important;
    }
    [data-testid="stButton"] button:hover,
    .stButton button:hover {
        background-color: var(--hf-btn-bg-hover) !important;
        border-color: var(--hf-btn-border) !important;
        color: var(--hf-btn-text) !important;
        transform: translateY(-1px);
    }
    /* expander 내부에서도 버튼 텍스트 색이 옅어지지 않도록 고정 */
    .stExpander [data-testid="stButton"] button,
    .stExpander .stButton button,
    .stExpander [data-testid="stButton"] button p,
    .stExpander .stButton button p {
        color: var(--hf-btn-text) !important;
    }
    [data-testid="stButton"] button:disabled,
    .stButton button:disabled {
        background: #ffffff !important;
        color: #ffffff !important;
        border-color: #d9e3d4 !important;
        opacity: 1 !important;
        box-shadow: none !important;
    }
    /* 기여도 보드 아이콘 가독성 보정 */
    [data-testid="stButton"] button {
        font-weight: 600 !important;
    }
    /* 출하 기여도 보드 아이콘 크기 강조 */
    [data-testid="stButton"] button[kind="secondary"][data-testid*="baseButton-secondary"] {
        font-size: 1.12rem !important;
        line-height: 1.1 !important;
    }
    .stSelectbox [data-baseweb="select"] {
        border-radius: 10px !important;
    }
    .contrib-board {
        display: flex;
        gap: 4px;
        align-items: flex-start;
        margin-top: 6px;
        margin-bottom: 8px;
    }
    .contrib-week {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .contrib-cell {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 2px;
        border: 1px solid rgba(43, 72, 30, 0.14);
        box-sizing: border-box;
    }
    /* 출하 기여도 보드 전용 버튼: key prefix 기반 레벨 색상 고정 */
    div[class*="st-key-pb-empty-"] button {
        background: #ffffff !important;
        border-color: #d9e3d4 !important;
        color: transparent !important;
    }
    div[class*="st-key-pb-lv1-"] button {
        background: #66bb6a !important; /* Lv1: 초록 */
        border-color: #4a9f50 !important;
        color: transparent !important;
    }
    div[class*="st-key-pb-lv2-"] button {
        background: #f4d35e !important; /* Lv2: 노랑 */
        border-color: #d2b047 !important;
        color: transparent !important;
    }
    div[class*="st-key-pb-lv3-"] button {
        background: #ef5350 !important; /* Lv3+: 빨강 */
        border-color: #d74242 !important;
        color: transparent !important;
    }
    div[class*="st-key-pb-empty-"] button p,
    div[class*="st-key-pb-lv1-"] button p,
    div[class*="st-key-pb-lv2-"] button p,
    div[class*="st-key-pb-lv3-"] button p {
        color: transparent !important;
    }
    div[class*="st-key-pb-lv1-"] button:hover,
    div[class*="st-key-pb-lv2-"] button:hover,
    div[class*="st-key-pb-lv3-"] button:hover {
        filter: brightness(1.05) !important;
        transform: none !important;
    }
    
    /* ☀️ [1단계] 라이트 모드: 따뜻한 곡식 들판 톤 */
    .stExpander {
        background-color: #f7f9f4 !important; /* 부드러운 연녹조 아이보리 */
        border: 1px solid #d0dad0 !important; /* 은은한 풀잎색 경계선 */
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 4px rgba(45,58,34,0.03) !important;
    }
    .stExpander summary p {
        color: #2d3a22 !important; /* 짙은 흙빛 이끼색 브라운 */
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    .stExpander div[data-testid="stExpanderDetails"] {
        background-color: #ffffff !important; /* 본문 영역은 깔끔한 순백색 */
        padding: 18px !important;
        border-radius: 0 0 12px 12px !important;
    }

    /* 🌙 [2단계] 다크 모드: 깊은 밤의 황금 들판 톤 */
    @media (prefers-color-scheme: dark) {
        .stExpander {
            background-color: #222a1d !important; /* 깊은 올리브 브라운 */
            border: 1px solid #3b4834 !important; /* 톤다운된 짚단색 경계선 */
            box-shadow: none !important;
        }
        .stExpander summary p {
            color: #f1f5ee !important; /* 눈이 편안한 크림 화이트 */
        }
        .stExpander div[data-testid="stExpanderDetails"] {
            background-color: #1b2117 !important; /* 본문 영역은 더 깊은 이끼색 */
        }
        /* 다크 토글 시 expander 내부 텍스트 가독성 보정 */
        .stExpander div[data-testid="stExpanderDetails"],
        .stExpander div[data-testid="stExpanderDetails"] *,
        .stExpander div[data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"],
        .stExpander div[data-testid="stExpanderDetails"] label {
            color: #eef6ec !important;
        }
        .stExpander div[data-testid="stExpanderDetails"] .stTextArea textarea {
            color: #eef6ec !important;
            background-color: #253022 !important;
            border: 1px solid #4b5b43 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 데이터 수집 (ttl 캐시로 라디오 전환 시 디스크 I/O 완화)
@st.cache_data(ttl=60)
def get_obsidian_count():
    try:
        draft_dirs: list[Path] = [WORKFLOW_STAGE_DIRS[STAGE_DRAFT]]
        legacy_draft_dir = LEGACY_WORKFLOW_STAGE_DIRS.get(STAGE_DRAFT)
        if legacy_draft_dir and legacy_draft_dir not in draft_dirs:
            draft_dirs.append(legacy_draft_dir)

        seen_paths: set[Path] = set()
        count = 0
        for directory in draft_dirs:
            if not directory.exists():
                continue
            for path in directory.rglob("*.md"):
                resolved = path.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                count += 1
        return count
    except Exception:
        return 0


@st.cache_data(ttl=60)
def get_publish_count():
    try:
        return len([path for path in PUBLISH_CONTENT_DIR.iterdir() if path.suffix == ".md"])
    except Exception:
        return 0


@st.cache_data(ttl=60)
def get_vector_data():
    """선택된 Vector DB에서 문서 목록을 조회해 캐시 가능한 dict로 반환합니다."""
    try:
        return get_vector_store_snapshot(limit=1000)
    except Exception:
        return 0, []


@st.cache_data(ttl=60)
def get_deleted_metadata_rows():
    try:
        return list_deleted_note_rows(limit=1000)
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_workflow_counts():
    try:
        return get_workflow_stage_counts()
    except Exception:
        return {}


def list_markdown_rows(directory: Path) -> list[dict]:
    """디렉터리의 md 파일을 compact id + 생성일로 묶습니다."""
    rows = []
    for path in directory.iterdir():
        if path.suffix != ".md":
            continue
        name = path.name
        created_ts = get_file_created_ts(path)
        rows.append(
            {
                "name": name,
                "path": str(path),
                "id": generate_compact_id(path),
                "created_ts": created_ts,
                "created_at": format_ts(created_ts),
            }
        )
    return rows


def list_markdown_rows_recursive(directories: list[Path]) -> list[dict]:
    """여러 디렉터리를 재귀 순회하며 md 파일 목록을 반환합니다."""
    rows: list[dict] = []
    seen_paths: set[Path] = set()
    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*.md"):
            resolved = path.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            name = path.name
            created_ts = get_file_created_ts(path)
            rows.append(
                {
                    "name": name,
                    "path": str(path),
                    "id": generate_compact_id(path),
                    "created_ts": created_ts,
                    "created_at": format_ts(created_ts),
                }
            )
    return rows


def vector_by_title(points: list[dict]) -> dict[str, dict]:
    """title(파일명) → payload 맵."""
    mapping = {}
    for point in points:
        payload = point.get("payload") or {}
        title = payload.get("title")
        if title:
            mapping[title] = payload
    return mapping


def render_board_header(columns: list[tuple[str, float]]) -> None:
    """[(라벨, 비율), ...] 형태의 게시판 헤더."""
    cols = st.columns([ratio for _, ratio in columns])
    for col, (label, _) in zip(cols, columns):
        with col:
            st.markdown(f"**{label}**")
    st.markdown(
        "<hr style='margin:4px 0px 12px 0px; border-top: 2px solid #5a6e4b;'>",
        unsafe_allow_html=True,
    )


def render_row_meta(columns: list[tuple[str, float]], values: list[str]) -> None:
    cols = st.columns([ratio for _, ratio in columns])
    for col, value in zip(cols, values):
        with col:
            st.caption(value)


def render_rag_sources(retrieved: list[dict], key_prefix: str = "rag") -> None:
    """답변 근거 참조 문서를 expander로 표시합니다. 연관도 임계값 이상만 최대 3개."""
    grains = [
        g for g in (retrieved or [])
        if (g.get("score") or 0) >= MIN_RETRIEVAL_SCORE
    ][:3]
    if not grains:
        return
    st.markdown("---")
    st.markdown("#### 📌 답변 근거 (참조 문서)")
    for idx, grain in enumerate(grains, start=1):
        payload = grain.get("payload") or {}
        score = grain.get("score") or 0.0
        harvest_id = payload.get("compact_id") or str(grain.get("id"))
        title = payload.get("title", "Unknown")
        with st.expander(f"[{idx}] {title}  ·  질문-문서 {score * 100:.1f}%"):
            st.caption(f"수확 번호: `{harvest_id}`")
            st.markdown("**원본 본문**")
            st.text_area(
                label="본문",
                value=payload.get("text") or "",
                height=120,
                disabled=True,
                key=f"{key_prefix}_body_{grain.get('id')}_{idx}",
                label_visibility="collapsed",
            )
            st.markdown("**AI 타작**")
            st.text_area(
                label="AI 타작",
                value=payload.get("ai_summary_and_tags") or "요약 없음",
                height=100,
                disabled=True,
                key=f"{key_prefix}_summary_{grain.get('id')}_{idx}",
                label_visibility="collapsed",
            )


def render_farm_hero(
    obsidian_count: int,
    vector_count: int,
    publish_count: int,
    vector_name: str,
    publish_name: str,
) -> None:
    """레퍼런스 톤의 농사형 히어로 배너."""
    st.markdown(
        f"""
        <div class="farm-hero">
            <div class="farm-hero-title">📦 HarvestFlow 지식 농장 제어 센터</div>
            <div class="farm-hero-subtitle">
                파종 → AI 타작 → 곳간 비축 → 출하까지, 들판 흐름처럼 한 화면에서 추적합니다.
            </div>
            <div class="farm-chip-wrap">
                <span class="farm-chip">🌱 {notes_app_name} 씨앗 {obsidian_count}개</span>
                <span class="farm-chip">🍎 {vector_name} 곳간 {vector_count}개</span>
                <span class="farm-chip">📦 {publish_name} 출하 {publish_count}개</span>
                <span class="farm-chip">🛫 여름 시즌 수확 모드</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def paginate_items(items: list, section_key: str, label: str) -> list:
    """공통 페이지네이션 UI를 렌더링하고 현재 페이지 아이템을 반환합니다."""
    if not items:
        return []

    size_key = f"{section_key}_page_size"
    page_key = f"{section_key}_page"
    size_options = [10, 20, 50, 100]
    default_size = 20

    if size_key not in st.session_state:
        st.session_state[size_key] = default_size
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    selected_size = st.selectbox(
        f"{label} 페이지 크기",
        size_options,
        key=size_key,
    )
    total_pages = max(1, ceil(len(items) / selected_size))
    current_page = int(st.session_state.get(page_key, 1))
    current_page = max(1, min(current_page, total_pages))

    nav_left, nav_center, nav_right = st.columns([1, 8, 1])
    with nav_left:
        if st.button(
            "📦 ◀ 이전",
            key=f"{section_key}_prev",
            disabled=current_page <= 1,
            use_container_width=True,
        ):
            current_page -= 1
    with nav_right:
        if st.button(
            "다음 ▶ 📦",
            key=f"{section_key}_next",
            disabled=current_page >= total_pages,
            use_container_width=True,
        ):
            current_page += 1

    current_page = max(1, min(current_page, total_pages))
    st.session_state[page_key] = current_page

    start = (current_page - 1) * selected_size
    end = min(start + selected_size, len(items))
    st.caption(f"{label}: {current_page}/{total_pages} 페이지 · {start + 1}-{end}/{len(items)}건")

    return items[start:end]


def _publish_intensity_level(count: int, max_count: int) -> int:
    """일별 출하량을 건수 구간 기반 0~4 단계 강도로 변환합니다."""
    if count <= 0:
        return 0
    # 고정 구간: 1~2(낮음), 3~4(중간), 5~7(높음), 8+(매우 높음)
    if count <= 2:
        return 1
    if count <= 4:
        return 2
    if count <= 7:
        return 3
    return 4


def render_publish_contribution_board(rows: list[dict]) -> dict | None:
    """출하 문서를 contribution 보드로 렌더링하고 선택 문서를 반환합니다."""
    if not rows:
        return None

    by_day: dict[str, list[dict]] = {}
    for row in rows:
        published_ts = row.get("published_ts")
        if not published_ts:
            continue
        day_key = datetime.fromtimestamp(float(published_ts)).date().isoformat()
        by_day.setdefault(day_key, []).append(row)

    if not by_day:
        return None

    # 최근 20주(140일) 기준으로 GitHub contribution과 유사한 보드 구성
    end_day = max(datetime.fromisoformat(d).date() for d in by_day)
    start_day = end_day - timedelta(days=139)
    start_day = start_day - timedelta(days=(start_day.weekday() + 1) % 7)  # 일요일 정렬

    all_days = [start_day + timedelta(days=i) for i in range(140)]
    max_count = max(len(by_day.get(day.isoformat(), [])) for day in all_days)

    def _level_range_text(level: int) -> str:
        matched = [
            c
            for c in range(1, max_count + 1)
            if _publish_intensity_level(c, max_count) == level
        ]
        if not matched:
            return "-"
        if len(matched) == 1:
            return f"{matched[0]}건"
        return f"{matched[0]}~{matched[-1]}건"

    st.caption("출하 기여도 보드 (hover: 제목 보기 / 클릭: 상세 보기)")
    legend_cols = st.columns([1.4, 2.1, 2.1, 2.1], gap="small")
    with legend_cols[0]:
        st.caption("레벨 범례")
    with legend_cols[1]:
        st.caption(f"Lv.1 (낮음): {_level_range_text(1)}")
    with legend_cols[2]:
        st.caption(f"Lv.2 (중간): {_level_range_text(2)}")
    with legend_cols[3]:
        lv3_text = _level_range_text(3)
        lv4_text = _level_range_text(4)
        if lv4_text == "-" or lv4_text == lv3_text:
            st.caption(f"Lv.3+ (높음): {lv3_text}")
        else:
            st.caption(f"Lv.3~4 (높음): {lv3_text}, {lv4_text}")

    week_cols = st.columns(20, gap="small")
    for week_idx, col in enumerate(week_cols):
        week_start = start_day + timedelta(days=week_idx * 7)
        with col:
            for day_offset in range(7):
                day = week_start + timedelta(days=day_offset)
                day_key = day.isoformat()
                day_rows = by_day.get(day_key, [])
                count = len(day_rows)
                level = _publish_intensity_level(count, max_count)
                title_preview = ", ".join(r.get("name", "-") for r in day_rows[:2])
                if count > 2:
                    title_preview += f" 외 {count - 2}건"
                tooltip = (
                    f"{day_key}\n출하 {count}건\n{title_preview}"
                    if count
                    else f"{day_key}\n출하 없음"
                )
                if count == 0:
                    st.button(
                        " ",
                        key=f"pb-empty-{day_key}",
                        help=tooltip,
                        disabled=True,
                        use_container_width=True,
                    )
                else:
                    level_key = "pb-lv1"
                    if level == 2:
                        level_key = "pb-lv2"
                    elif level >= 3:
                        level_key = "pb-lv3"
                    if st.button(
                        " ",
                        key=f"{level_key}-{day_key}",
                        help=tooltip,
                        disabled=False,
                        use_container_width=True,
                    ):
                        st.session_state["publish_selected_day"] = day_key

    selectable_days = sorted(by_day.keys())
    selected_day = st.session_state.get("publish_selected_day")
    if selected_day not in by_day:
        selected_day = selectable_days[-1]
    st.session_state["publish_selected_day"] = selected_day

    candidates = sorted(
        by_day[selected_day],
        key=lambda r: (r.get("published_ts") or 0, r.get("ai_ts") or 0),
        reverse=True,
    )
    if len(candidates) == 1:
        return candidates[0]

    option_labels = [
        f"{row.get('id')} | {row.get('name')} | {row.get('published_at')}" for row in candidates
    ]
    selected_idx = st.selectbox(
        "같은 날짜 출하 문서",
        options=range(len(candidates)),
        format_func=lambda i: option_labels[i],
        key="publish_selected_doc_index",
    )
    return candidates[selected_idx]


# 데이터 로드
obsidian_cnt = get_obsidian_count()
publish_cnt = get_publish_count()
notes_app_name = NOTES_APP_NAME.title()
vector_db_name = VECTOR_DB_CLIENT.title()
publish_name = PUBLISH_CLIENT.title()
vector_cnt, vector_points = get_vector_data()
payload_by_title = vector_by_title(vector_points)
render_farm_hero(obsidian_cnt, vector_cnt, publish_cnt, vector_db_name, publish_name)

# ====================================================================
# 💾 [왼쪽 사이드바] 지식 농사 전체 통계 및 아웃라인 선택 메뉴
# ====================================================================
st.sidebar.title("👩‍🌾🥕 지식 농사 환경")

st.sidebar.subheader("📊 금년도 수확 지표")
st.sidebar.metric(label=f"🌱 심겨진 씨앗 ({notes_app_name})", value=f"{obsidian_cnt} 개")
st.sidebar.metric(label=f"🍎 비축된 지식 곳간 ({vector_db_name} RAG)", value=f"{vector_cnt} 개")
st.sidebar.metric(label=f"📦 수확된 황금 곡식 ({publish_name})", value=f"{publish_cnt} 개")

workflow_counts = get_workflow_counts()
st.sidebar.subheader("🧭 워크플로우 단계 현황")
st.sidebar.markdown(
    f"""
    <div class="workflow-stage-card">
      <div class="workflow-stage-grid">
        <div class="workflow-stage-item"><span class="workflow-stage-key">초안</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_DRAFT, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">검수요청</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_REVIEW_REQUEST, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">출간대기</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_PUBLISH_WAIT, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">수정필요</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_NEEDS_FIX, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">2차완료</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_SECOND_REVIEW_DONE, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">출간완료</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_PUBLISHED, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">수정대기</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_REVISE_WAIT, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">삭제요청</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_DELETE_REQUEST, 0)}건</span></div>
        <div class="workflow-stage-item"><span class="workflow-stage-key">휴지통</span><span class="workflow-stage-val">{workflow_counts.get(STAGE_TRASH, 0)}건</span></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")

st.sidebar.subheader("📂 지식 대지 조회")
notes_stage_label = f"🌱 씨앗 단계 ({notes_app_name})"
vector_stage_label = f"🌾 곳간 단계 ({vector_db_name} RAG)"
publish_stage_label = f"🚚 출하 단계 ({publish_name})"
deleted_stage_label = "🗃️ 삭제 이력 (메타DB)"

menu_selection = st.sidebar.radio(
    "조회할 지식 단계를 선택하세요",
    ["전체 농사 관제", notes_stage_label, vector_stage_label, publish_stage_label, deleted_stage_label],
    key="menu_selection",
)

# ====================================================================
# 🖥️ [메인 화면] 농업 라이프사이클에 맞춘 게시판 인터페이스
# ====================================================================

SEED_COLS = [
    ("씨앗번호", 1.4),
    ("곡식명", 2.6),
    ("파일 생성일", 1.4),
]
GRANARY_COLS = [
    ("수확 번호", 1.4),
    ("곡식명", 2.2),
    ("파일 생성일", 1.2),
    ("AI 타작일", 1.2),
]
SHIP_COLS = [
    ("출하 번호", 1.3),
    ("곡식명", 1.8),
    ("파일 생성일", 1.1),
    ("AI 타작일", 1.1),
    ("블로그 출간일", 1.1),
]
DELETED_COLS = [
    ("곡식명", 2.4),
    ("마지막 수정시각", 1.6),
    ("상태", 1.0),
]

# 1. 전체 풍년 관제 메뉴
if menu_selection == "전체 농사 관제":
    st.header("📋 지식 생태계 통합 수확 정보")
    st.info("💡 알곡 제목을 클릭하면 온디바이스 AI 농부가 정교하게 껍질을 깎아내고 분류한 타작(요약) 상세 데이터가 확장됩니다.")

    if not vector_points:
        st.warning("아직 파이프라인에 파종된 지식이 없습니다. 로컬 마크다운에 글을 쓰고 프론트매터 속성을 '출간'으로 변경해 보세요!")
    else:
        # AI 타작일 기준 최신순
        points = sorted(
            vector_points,
            key=lambda p: parse_iso_ts((p.get("payload") or {}).get("ai_processed_at")),
            reverse=True,
        )
        points = paginate_items(points, "all_harvest", "통합 수확 목록")
        render_board_header(GRANARY_COLS)
        for point in points:
            payload = point["payload"] or {}
            point_id = payload.get("compact_id") or str(point["id"])
            title = payload.get("title", "Unknown")
            created_at = payload.get("created_at", "-")
            ai_at = payload.get("ai_processed_at", "-")
            ai_data = payload.get("ai_summary_and_tags", "요약 데이터가 비어 있습니다.")

            with st.expander(f"{point_id}  |  📦 {title}"):
                render_row_meta(GRANARY_COLS, [point_id, title, created_at, ai_at])
                st.text_area(
                    label="AI 타작 및 정제 데이터 본문",
                    value=ai_data,
                    height=130,
                    disabled=True,
                    key=f"all_{point_id}",
                )

    st.markdown("---")
    st.header("🚜 실시간 지식 농사 일지 (인프라 로그)")

    log_text = read_recent_logs(30)
    if log_text:
        st.text_area(
            label="백그라운드 파이프라인 I/O 및 AI 추론 트래킹",
            value=log_text,
            height=250,
            disabled=True,
            key="system_log_view",
        )
    else:
        st.info("아직 생성된 농사 일지(로그)가 없습니다. 파이프라인이 구동되면 기록이 시작됩니다.")

    if st.button("📦 일지 새로고침"):
        st.rerun()

# 2. 🌱 씨앗 단계
elif menu_selection == f"🌱 씨앗 단계 ({notes_app_name})":
    st.header(f"🌱 {notes_app_name} 보관소 내 파종 대기 중")
    try:
        draft_dirs: list[Path] = [WORKFLOW_STAGE_DIRS[STAGE_DRAFT]]
        legacy_draft_dir = LEGACY_WORKFLOW_STAGE_DIRS.get(STAGE_DRAFT)
        if legacy_draft_dir and legacy_draft_dir not in draft_dirs:
            draft_dirs.append(legacy_draft_dir)
        rows = list_markdown_rows_recursive(draft_dirs)
        if not rows:
            st.warning("아직 초안 단계에 뿌려진 마크다운 씨앗(파일)이 없습니다.")
        else:
            rows.sort(key=lambda r: r["created_ts"], reverse=True)
            rows = paginate_items(rows, "seed_stage", "씨앗 목록")
            render_board_header(SEED_COLS)
            for row in rows:
                with st.expander(f"{row['id']}  |  🫛 {row['name']}"):
                    render_row_meta(SEED_COLS, [row["id"], row["name"], row["created_at"]])
                    st.write(f"로컬 저장 경로: `{row['path']}`")
                    st.caption("※ 본 파일은 가공되지 않은 날것의 지식 씨앗입니다. AI 타작 결과물을 보시려면 '전체 풍년 관제' 메뉴를 이용하세요.")
    except Exception as e:
        st.error(f"지식 대지 파일 로드 실패: {e}")

# 3. 🍎 곳간 단계 (Vector DB)
elif menu_selection == vector_stage_label:
    st.header(f"🌾 {vector_db_name} 지식 곳간")

    # st.subheader("🧠 온디바이스 AI 지식 비서 (RAG)")
    st.markdown(
        "의미론적 RAG 검색 레이어로, 로컬 메모 내용만으로 답합니다. "
        "외부로 데이터가 나가지 않는 온디바이스 검색입니다."
    )
    st.caption(
        f"임베딩: `nomic-embed-text` · 생성: `{RAG_MODEL}` "
        f"(파이프라인 요약: `{PIPELINE_MODEL}`) · "
        "예전에 더미 벡터로 쌓인 노트는 아래 재색인이 필요합니다."
    )

    # text_input 생성 전에만 session_state[rag_search_input] 수정 가능
    if "rag_pending_query" in st.session_state:
        st.session_state["rag_search_input"] = st.session_state.pop("rag_pending_query")

    user_question = st.text_input(
        "🔍 지식 곳간에 물어보기",
        placeholder="예: Redis 소켓 타임아웃은 어떻게 해결했지?",
        key="rag_search_input",
    )

    if st.button("📦 벡터 재색인", help="payload 본문을 nomic 임베딩으로 다시 저장"):
        with st.spinner("창고 알곡을 다시 도정(임베딩)하는 중..."):
            try:
                updated = reindex_all_embeddings()
                st.success(f"재색인 완료: {updated}건")
                get_vector_data.clear()
            except Exception as e:
                st.error(f"재색인 실패: {e}")

    if user_question:
        cached = None
        with st.spinner("시맨틱 캐시에서 비슷한 과거 질문을 찾는 중..."):
            try:
                cached = get_cached_answer(user_question)
            except Exception as e:
                st.warning(f"캐시 조회 실패(RAG로 계속): {e}")

        if cached and cached.get("answer"):
            q_sim = (cached.get("score") or 0) * 100  # 현재 질문 ↔ 과거 질문
            sources = cached.get("sources") or []
            if not sources:
                try:
                    sources = search_knowledge_base(user_question, limit=3)
                except Exception:
                    sources = []

            a_sim = cached.get("answer_similarity") or 0
            if not a_sim and sources:
                try:
                    a_sim = compute_answer_similarity(cached["answer"], sources)
                except Exception:
                    a_sim = 0

            st.markdown("### 📚 곳간에서 찾은 답")
            st.caption(
                f"⚡ 시맨틱 캐시 · "
                f"질문 유사도(과거 질문): **{q_sim:.1f}%** · "
                f"답변 유사도(근거 문서): **{a_sim * 100:.1f}%**"
            )
            st.caption(f"유사 과거 질문: “{cached.get('past_query')}”")
            st.info(cached["answer"])
            if sources:
                render_rag_sources(sources, key_prefix="cache")
            else:
                st.caption("이 캐시에는 참조 문서가 저장되어 있지 않습니다.")
        else:
            retrieved: list[dict] = []
            with st.spinner("지식 곳간에서 관련 알곡을 검색하는 중..."):
                try:
                    retrieved = search_knowledge_base(user_question, limit=3)
                except Exception as e:
                    st.error(f"검색 실패: {e}")

            if not retrieved:
                st.warning("질문과 연관된 지식을 찾지 못했습니다. 관련 메모를 먼저 출간해 주세요.")
            else:
                q_sim = (retrieved[0].get("score") or 0) * 100  # 질문 ↔ 1순위 문서
                st.markdown("### 🤖 AI 농부의 답변")
                meta_box = st.empty()
                answer_box = st.empty()
                meta_box.caption(
                    f"질문 유사도(근거 문서): **{q_sim:.1f}%** · "
                    "답변 유사도(근거 문서): 계산 중…"
                )

                pieces: list[str] = []
                for piece in iter_rag_answer(user_question, retrieved):
                    pieces.append(piece)
                    answer_box.info("".join(pieces))

                full_answer = "".join(pieces).strip()
                a_sim = 0.0
                if full_answer:
                    try:
                        a_sim = compute_answer_similarity(full_answer, retrieved)
                    except Exception as e:
                        st.caption(f"답변 유사도 계산 실패: {e}")

                    meta_box.caption(
                        f"질문 유사도(근거 문서): **{q_sim:.1f}%** · "
                        f"답변 유사도(근거 문서): **{a_sim * 100:.1f}%**"
                    )
                    try:
                        save_to_cache(
                            user_question,
                            full_answer,
                            sources=retrieved,
                            doc_similarity=retrieved[0].get("score") or 0,
                            answer_similarity=a_sim,
                        )
                    except Exception as e:
                        st.caption(f"캐시 저장 실패: {e}")

                render_rag_sources(retrieved, key_prefix="fresh")

    # 최근 질의 히스토리 (캐시 재활용용)
    with st.expander("📜 최근 질의 캐시 (클릭하면 입력창에 재활용)", expanded=False):
        try:
            history = list_recent_cached_queries(limit=15)
        except Exception as e:
            history = []
            st.caption(f"히스토리 로드 실패: {e}")

        if not history:
            st.caption("아직 저장된 질의가 없습니다. 질문을 한 번 하면 여기에 쌓입니다.")
        else:
            for row in history:
                past = row.get("past_query") or ""
                cols = st.columns([4, 1])
                with cols[0]:
                    st.markdown(f"**{past}**")
                    st.caption(row.get("cached_at") or "")
                with cols[1]:
                    if st.button("📦 재사용", key=f"reuse_{row.get('id')}"):
                        st.session_state["rag_pending_query"] = past
                        st.rerun()

    st.markdown("---")
    st.subheader("📋 곳간 적재 목록")

    if not vector_points:
        st.warning("지식 곳간에 비축된 영양분(벡터 데이터)이 아직 없습니다.")
    else:
        # 1순위 AI 타작일, 2순위 파일 생성일
        points = sorted(
            vector_points,
            key=lambda p: (
                parse_iso_ts((p.get("payload") or {}).get("ai_processed_at")),
                parse_iso_ts((p.get("payload") or {}).get("created_at")),
            ),
            reverse=True,
        )
        points = paginate_items(points, "granary_stage", "곳간 적재 목록")
        render_board_header(GRANARY_COLS)
        for point in points:
            payload = point["payload"] or {}
            # 운영 키는 compact_id 통일, 내부 vector point id는 참조용
            harvest_id = payload.get("compact_id") or str(point["id"])
            title = payload.get("title", "Unknown")
            created_at = payload.get("created_at", "-")
            ai_at = payload.get("ai_processed_at", "-")

            with st.expander(f"{harvest_id}  |  🍎 {title}"):
                render_row_meta(GRANARY_COLS, [harvest_id, title, created_at, ai_at])
                st.text_area(
                    label="AI 타작 및 정제 데이터 본문",
                    value=payload.get("ai_summary_and_tags", "요약 데이터가 비어 있습니다."),
                    height=130,
                    disabled=True,
                    key=f"granary_{harvest_id}",
                )

# 4. 🚚 출하 단계 (Publish)
elif menu_selection == publish_stage_label:
    st.header(f"📦 {publish_name} 채널로 출하된 작물 목록")
    try:
        rows = list_markdown_rows(PUBLISH_CONTENT_DIR)
        if not rows:
            st.warning("출하된 곡식이 없습니다. 파이프라인 추적 데몬이 구동되면 이곳으로 최종 인입됩니다.")
        else:
            enriched = []
            for row in rows:
                payload = payload_by_title.get(row["name"], {})
                published_at = payload.get("published_at") or format_ts(
                    Path(row["path"]).stat().st_mtime
                )
                ai_at = payload.get("ai_processed_at", "-")
                created_at = payload.get("created_at") or row["created_at"]
                enriched.append(
                    {
                        **row,
                        "created_at": created_at,
                        "ai_at": ai_at,
                        "published_at": published_at,
                        "published_ts": parse_iso_ts(str(published_at))
                        or Path(row["path"]).stat().st_mtime,
                        "ai_ts": parse_iso_ts(ai_at),
                        "created_sort": parse_iso_ts(created_at) or row["created_ts"],
                    }
                )

            # 1순위 블로그 출간일, 2순위 AI 타작일, 3순위 파일 생성일
            enriched.sort(
                key=lambda r: (r["published_ts"], r["ai_ts"], r["created_sort"]),
                reverse=True,
            )
            left, right = st.columns([3, 2], gap="large")
            with left:
                selected_row = render_publish_contribution_board(enriched)
            with right:
                st.subheader("출하된 곡식 정보")
                if not selected_row:
                    st.caption("왼쪽 contribution 셀을 클릭하면 상세 정보가 표시됩니다.")
                else:
                    st.markdown(
                        f"""
                        <div class="publish-info-card">
                            <div class="publish-info-row">
                                <span class="publish-info-key">id</span>
                                <span class="publish-info-value">{selected_row.get('id', '-')}</span>
                            </div>
                            <div class="publish-info-row">
                                <span class="publish-info-key">filename</span>
                                <span class="publish-info-value">{selected_row.get('name', '-')}</span>
                            </div>
                            <div class="publish-info-row">
                                <span class="publish-info-key">파일 생성일</span>
                                <span class="publish-info-value">{selected_row.get('created_at', '-')}</span>
                            </div>
                            <div class="publish-info-row">
                                <span class="publish-info-key">블로그 출간일</span>
                                <span class="publish-info-value">{selected_row.get('published_at', '-')}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    except Exception as e:
        st.error(f"출하 폴더 로드 실패: {e}")

# 5. 🗃️ 삭제 이력 (soft delete)
elif menu_selection == deleted_stage_label:
    st.header("🗃️ 메타데이터 삭제 이력")
    st.caption("노트 파일 삭제/이동 시 notes 테이블의 `deleted=1`로 남긴 이력입니다.")
    if st.button("📦 삭제 이력 새로고침", key="deleted_stage_refresh"):
        get_deleted_metadata_rows.clear()
        st.rerun()

    rows = get_deleted_metadata_rows()
    if not rows:
        st.info("현재 삭제 이력이 없습니다.")
    else:
        now_ts = datetime.now().timestamp()
        total_count = len(rows)
        recent_24h = sum(
            1 for row in rows
            if (row.get("last_modified") or 0) >= now_ts - (24 * 60 * 60)
        )
        recent_7d = sum(
            1 for row in rows
            if (row.get("last_modified") or 0) >= now_ts - (7 * 24 * 60 * 60)
        )
        summary_cols = st.columns(3)
        summary_cols[0].metric("누적 삭제 이력", f"{total_count}건")
        summary_cols[1].metric("최근 24시간", f"{recent_24h}건")
        summary_cols[2].metric("최근 7일", f"{recent_7d}건")

        filter_cols = st.columns([1.2, 1.8], gap="small")
        with filter_cols[0]:
            period_label = st.selectbox(
                "기간 필터",
                ["전체", "최근 24시간", "최근 7일", "최근 30일"],
                key="deleted_period_filter",
            )
        with filter_cols[1]:
            filename_query = st.text_input(
                "파일명 검색",
                placeholder="예: Redis 또는 .md 파일명 일부",
                key="deleted_filename_query",
            ).strip().lower()

        if period_label == "최근 24시간":
            min_ts = now_ts - (24 * 60 * 60)
            rows = [row for row in rows if (row.get("last_modified") or 0) >= min_ts]
        elif period_label == "최근 7일":
            min_ts = now_ts - (7 * 24 * 60 * 60)
            rows = [row for row in rows if (row.get("last_modified") or 0) >= min_ts]
        elif period_label == "최근 30일":
            min_ts = now_ts - (30 * 24 * 60 * 60)
            rows = [row for row in rows if (row.get("last_modified") or 0) >= min_ts]

        if filename_query:
            rows = [
                row for row in rows
                if filename_query in str(row.get("filename", "")).lower()
            ]

        if not rows:
            st.info("필터 조건에 맞는 삭제 이력이 없습니다.")
        else:
            rows = paginate_items(rows, "deleted_stage", "삭제 이력")
            render_board_header(DELETED_COLS)
            for row in rows:
                filename = row.get("filename", "-")
                last_modified = row.get("last_modified", 0)
                modified_at = format_ts(last_modified) if last_modified else "-"
                status = row.get("status", "-")
                with st.expander(f"🪦 {filename}"):
                    render_row_meta(
                        DELETED_COLS,
                        [filename, modified_at, status],
                    )

