# check_qdrant.py
from qdrant_client import QdrantClient

# 로컬 저장소 연결
client = QdrantClient(path="./qdrant_local")

# 1. 컬렉션 정보 조회 (데이터가 몇 개 쌓였는지 확인)
info = client.get_collection(collection_name="obsidian_notes")
print(f"📊 현재 Qdrant에 저장된 총 노트 수: {info.points_count}개")

# 2. 저장된 실제 데이터 10개 가져와서 출력
scroll_result, _ = client.scroll(
    collection_name="obsidian_notes",
    limit=10,
    with_payload=True,
    with_vectors=False # 화면 복잡도를 위해 벡터 값은 숨김
)

print("\n🔍 [Qdrant 적재 데이터 목록]")
for point in scroll_result:
    payload = point.payload
    print(f"- ID: {point.id}")
    print(f"  제목: {payload.get('title')} | 상태: {payload.get('status')}")
    print(f"  🤖 AI 분석 데이터:\n{payload.get('ai_summary_and_tags')}")
    print("-" * 40)