import sqlite3
import hashlib
import numpy as np
import subprocess
import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

DB_FILE = "pipeline_metadata.db"
# 서버 없는 파일 기반 초경량 Qdrant 벡터 DB 세팅

def get_qdrant_client():
    """필요할 때만 안전하게 클라이언트를 생성해서 반환"""
    # 파일 동시 접근 잠금을 우회하기 위해 인스턴스 옵션 추가
    return QdrantClient(path="./qdrant_local", prefer_grpc=False)

def init_infrastructure():
    """SQLite 및 Qdrant 컬렉션 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS notes (filename TEXT PRIMARY KEY, last_modified REAL, status TEXT)')
    conn.commit()
    conn.close()

    # 🚀 전역변수 대신 함수 호출로 변경
    client = get_qdrant_client()
    if not client.collection_exists("obsidian_notes"):
        client.create_collection(
            collection_name="obsidian_notes",
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    client.close() # 초기화 후 즉시 닫기

def update_meta_db(filename, mtime, status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO notes VALUES (?, ?, ?)', (filename, mtime, status))
    conn.commit()
    conn.close()

def save_to_vector_db(note_id, text, metadata):
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    seed = int(text_hash[:8], 16)
    
    np.random.seed(seed)
    dummy_vector = np.random.rand(768).tolist()
    point_id = int(hashlib.sha256(note_id.encode('utf-8')).hexdigest()[:12], 16)

    # 🚀 저장할 때만 잠깐 열어서 쓰고 닫기
    client = get_qdrant_client()
    client.upsert(
        collection_name="obsidian_notes",
        points=[PointStruct(id=point_id, vector=dummy_vector, payload={"text": text, **metadata})]
    )
    client.close()

def upload_to_github():
    """AI 정제가 완료된 Quartz 콘텐츠 폴더를 GitHub에 자동으로 푸시하여 블로그 업로드"""
    print("🚀 [블로그 업로드] 최신 정제 문서를 GitHub 저장소로 업로드를 시작합니다...")
    try:
        # 1. 변경된 마크다운 파일들 스테이징
        subprocess.run(["git", "add", "quartz_content/*"], check=True)
        
        # 2. 현재 시간을 담은 코밋 메시지 생성
        commit_msg = f"📰 블로그 자동 발행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # 3. GitHub 원격 저장소로 푸시 (메인 브랜치명 확인 필수: main 또는 master)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ [업로드 완료] GitHub 원격 저장소로 동기화되었습니다. 잠시 후 웹사이트에 반영됩니다.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ [업로드 실패] Git 명령어 실행 중 에러가 발생했습니다: {e}")
    except Exception as e:
        print(f"❌ [업로드 오류] 예상치 못한 오류: {e}")