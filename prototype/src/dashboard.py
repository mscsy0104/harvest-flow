import streamlit as st
import os
from qdrant_client import QdrantClient

# 1. 페이지 기본 설정 및 스타일 정의
st.set_page_config(page_title="AI Pipeline Monitor", layout="wide")

# CSS를 활용해 게시판 리스트 디자인을 조금 더 깔끔하게 튜닝
st.markdown("""
    <style>
    /* 메인 화면 여백 조정 */
    .reportview-container .main .block-container { padding-top: 2rem; }
    
    /* ☀️ [1단계] 기본 모드 (라이트 모드 또는 확장 프로그램 미작동 시) */
    .stExpander {
        background-color: #f8fafc !important; /* 부드러운 연한 그레이 배경 */
        border: 1px solid #e2e8f0 !important; /* 깔끔한 경계선 */
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }
    .stExpander summary p {
        color: #1e293b !important; /* 짙은 네이비/블랙 글자색 */
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .stExpander div[data-testid="stExpanderDetails"] {
        background-color: #ffffff !important; /* 내부 영역은 순백색 */
        padding: 15px !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* 🌙 [2단계] 시스템/브라우저가 다크 모드일 때 (동적 전환) */
    @media (prefers-color-scheme: dark) {
        .stExpander {
            background-color: #1e222b !important; /* 어두운 대시보드용 그레이 */
            border: 1px solid #3f444e !important; /* 다크모드용 경계선 */
        }
        .stExpander summary p {
            color: #f1f3f5 !important; /* 선명한 화이트 글자색 */
        }
        .stExpander div[data-testid="stExpanderDetails"] {
            background-color: #15181f !important; /* 내부 영역은 더 깊은 블랙 계열 */
        }
    }
    </style>
""", unsafe_allow_html=True)
# st.markdown("""
#     <style>
#     .reportview-container .main .block-container { padding-top: 2rem; }
#     .stExpander { background-color: #f9fbfd; border: 1px solid #e1e8ed; border-radius: 6px; margin-bottom: 8px; }
#     </style>
# """, unsafe_allow_html=True)

st.title("AI 지식 인프라 파이프라인 관제탑")
st.markdown("옵시디언 데이터 생성부터 AI 가공, 벡터 적재, 블로그 발행까지의 전체 인프라 상태를 모니터링합니다.")
st.markdown("---")

# 2. 인프라 연결 및 환경 변수 설정 (기존 설정 연동)
VAULT_DIR = "./obsidian_vault"
BLOG_DIR = "./quartz_content"


# 3. 실시간 데이터 수집 함수들
def get_obsidian_count():
    try:
        return len([f for f in os.listdir(VAULT_DIR) if f.endswith('.md')])
    except Exception:
        return 0

def get_quartz_count():
    try:
        return len([f for f in os.listdir(BLOG_DIR) if f.endswith('.md')])
    except Exception:
        return 0

def get_qdrant_data():
    """대시보드가 새로고침될 때만 잠깐 Qdrant 파일을 열어서 데이터를 긁어옴"""
    try:
        # 🚀 호출 시점에만 생성하고 다 쓰면 닫히도록 유도
        client = QdrantClient(path="./qdrant_local", prefer_grpc=False)
        info = client.get_collection(collection_name="obsidian_notes")
        points_count = info.points_count
        scroll_result, _ = client.scroll(
            collection_name="obsidian_notes", limit=100, with_payload=True, with_vectors=False
        )
        client.close() # 🔓 조회가 끝나면 즉시 파일 잠금 해제!
        return points_count, scroll_result
    except Exception as e:
        return 0, []

# 데이터 로드
obsidian_cnt = get_obsidian_count()
quartz_cnt = get_quartz_count()
qdrant_cnt, qdrant_points = get_qdrant_data()

# ====================================================================
# 💾 [왼쪽 사이드바] 전체 통계 수치 및 데이터 소스 선택 메뉴
# ====================================================================
st.sidebar.title("⚙️ 시스템 인프라")

# 사이드 통계 수치 배치
st.sidebar.subheader("📊 부문별 데이터 수")
st.sidebar.metric(label="📁 Obsidian Vault (원천)", value=f"{obsidian_cnt} 개")
st.sidebar.metric(label="🧠 Qdrant DB (AI 적재)", value=f"{qdrant_cnt} 개")
st.sidebar.metric(label="🌐 Quartz Blog (최종 발행)", value=f"{quartz_cnt} 개")

st.sidebar.markdown("---")

# 통계 수치 밑에 배치하는 소스 선택 메뉴
st.sidebar.subheader("📂 데이터 아웃라인 조회")
menu_selection = st.sidebar.radio(
    "출출처 관점을 선택하세요",
    ["전체 종합 관제", "📁 Obsidian Vault 전용", "🧠 Qdrant DB 전용", "🌐 Quartz Blog 전용"]
)

# ====================================================================
# 🖥️ [메인 화면] 선택한 메뉴에 따른 게시판 형태의 드롭다운 UI 시각화
# ====================================================================

# 게시판 헤더 출력용 헬퍼 함수
def render_board_header():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("**데이터 고유 ID / 해시**")
    with col2:
        st.markdown("**문서 제목 (클릭 시 AI 정제 상세 내용 확산)**")
    st.markdown("<hr style='margin:4px 0px 12px 0px; border-top: 2px solid #333;'>", unsafe_allow_html=True)

# 1. 전체 종합 관제 메뉴
if menu_selection == "전체 종합 관제":
    st.header("📋 인프라 데이터 통합 게시판")
    st.info("💡 제목을 클릭하면 하단에 로컬 LLM(Gemma4)이 추출한 요약 및 해시태그 상세 정보가 드롭다운됩니다.")
    
    if not qdrant_points:
        st.warning("파이프라인을 관통한 데이터가 아직 없습니다. 옵시디언에 글을 쓰고 '출간' 상태로 변경해 보세요!")
    else:
        render_board_header()
        for point in qdrant_points:
            payload = point.payload
            title = payload.get('title', 'Unknown')
            ai_data = payload.get('ai_summary_and_tags', '요약 데이터가 비어 있습니다.')
            
            # st.expander가 질문하신 '누르면 드롭다운되는 게시판' 역할을 완벽히 수행합니다.
            # 앞에 ID와 제목이 수평으로 보이도록 트릭 배치
            with st.expander(f"🆔 {point.id} ⠀⠀|⠀⠀ 📝 {title}"):
                st.markdown("**🤖 구글 Gemma4 기반 지능형 정제 로그**")
                st.text_area(label="AI 가공 데이터 본문", value=ai_data, height=130, disabled=True, key=f"all_{point.id}")

# 2. Obsidian Vault 전용 메뉴
elif menu_selection == "📁 Obsidian Vault 전용":
    st.header("📁 Obsidian 로컬 보관소 내 마크다운 파일 목록")
    try:
        files = [f for f in os.listdir(VAULT_DIR) if f.endswith('.md')]
        if not files:
            st.warning("Obsidian Vault 폴더가 비어 있습니다.")
        else:
            render_board_header()
            for idx, f in enumerate(files):
                with st.expander(f"🆔 로컬인덱스_{idx+1:03d} ⠀⠀|⠀⠀ 📄 {f}"):
                    st.write(f"경로: `{os.path.join(VAULT_DIR, f)}`")
                    st.caption("※ 이 데이터는 원천 파일입니다. AI 가공본을 보시려면 '전체 종합 관제' 혹은 'Qdrant' 메뉴를 선택하세요.")
    except Exception as e:
        st.error(f"폴더 로드 실패: {e}")

# 3. Qdrant DB 전용 메뉴
elif menu_selection == "🧠 Qdrant DB 전용":
    st.header("🧠 Qdrant 벡터 데이터베이스 검색 레이어")
    if not qdrant_points:
        st.warning("Qdrant DB에 임베딩된 벡터 데이터가 없습니다.")
    else:
        render_board_header()
        for point in qdrant_points:
            payload = point.payload
            with st.expander(f"🆔 {point.id} ⠀⠀|⠀⠀ 🧠 {payload.get('title')}"):
                st.json({
                    "Qdrant_Point_ID": point.id,
                    "Payload_Title": payload.get('title'),
                    "Pipeline_Status": payload.get('status'),
                    "AI_Refined_Text": payload.get('ai_summary_and_tags')
                })

# 4. Quartz Blog 전용 메뉴
elif menu_selection == "🌐 Quartz Blog 전용":
    st.header("🌐 Quartz 배포 대기 중인 엔드포인트 파일 목록")
    try:
        files = [f for f in os.listdir(BLOG_DIR) if f.endswith('.md')]
        if not files:
            st.warning("Quartz 배포 폴더가 비어 있습니다. 파이프라인이 작동해야 파일이 인입됩니다.")
        else:
            render_board_header()
            for idx, f in enumerate(files):
                with st.expander(f"🆔 웹퍼블리시_{idx+1:03d} ⠀⠀|⠀⠀ 🌐 {f}"):
                    st.success(f"현재 로컬 정적 블로그(`localhost:1313`)에 정상 퍼블리싱 완료된 문서입니다.")
                    st.caption(f"배포 파일 타겟 경로: `{os.path.join(BLOG_DIR, f)}`")
    except Exception as e:
        st.error(f"폴더 로드 실패: {e}")