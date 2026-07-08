import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 모듈화한 스크립트 로드
from src.parser import parse_markdown
from src.database import init_infrastructure, update_meta_db, save_to_vector_db
from src.agent import generate_ai_metadata

VAULT_DIR = "./obsidian_vault"
BLOG_DIR = "./quartz_content"

def pipeline_trigger(file_path):
    filename = os.path.basename(file_path)
    
    # 1. 마크다운 파일 파싱
    meta, body_text, yaml_text = parse_markdown(file_path)
    
    # 2. '출간' 조건 검사
    if meta and meta.get("status") == "출간":
        mtime = os.path.getmtime(file_path)
        print(f"\n⚡⚡ [파이프라인 가동] '{filename}' 검사 중...")

        # 3. 로컬 Ollama 에이전트 작동
        ai_refined = generate_ai_metadata(body_text)
        
        # 4. Quartz 배포용 마크다운 최종 조립
        processed_content = (
            "---\n"
            f"{yaml_text.strip()}\n"
            "---\n\n"
            f"### 🤖 AI 자동 요약 및 인덱싱\n"
            f"{ai_refined.strip()}\n\n"
            "---\n\n"
            f"### 본문\n"
            f"{body_text.strip()}"
        )
        
        # 5. 블로그 배포 파일 쓰기
        target_path = os.path.join(BLOG_DIR, filename)
        with open(target_path, "w", encoding="utf-8") as target_file:
            target_file.write(processed_content)
        
        # 6. 인프라 DB 저장 (메타데이터 SQLite + 벡터 DB Qdrant 동시 적재)
        update_meta_db(filename, mtime, "출간")
        qdrant_payload = {
            "title": filename,
            "status": "출간",
            "ai_summary_and_tags": ai_refined.strip()  # ◀ AI가 생성한 텍스트 추가!
        }
        save_to_vector_db(filename, body_text, qdrant_payload)

        print(f"🎉 [엔드투엔드 완료] '{filename}'이(가) AI 정제 후 블로그 및 Qdrant에 적재되었습니다.")
        
        print(f"🎉 [엔드투엔드 완료] '{filename}'이(가) AI 정제 후 블로그로 발행되었습니다.")

        # 🚀 [최종 퍼즐 연결] 로컬 작업이 완벽히 끝났으니 이제 깃허브로 밀어 올립니다!
        from src.database import upload_to_github
        upload_to_github()

class ObsidianHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            time.sleep(0.5)  # I/O 버퍼 안정화 시간 확보
            pipeline_trigger(event.src_path)

if __name__ == "__main__":
    init_infrastructure()
    print(f"👁️  모듈화된 지능형 AI 파이프라인 엔진 가동 중... ({VAULT_DIR})")
    
    event_handler = ObsidianHandler()
    observer = Observer()
    observer.schedule(event_handler, path=VAULT_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 사용자 요청으로 종료 신호를 수신했습니다.")
    finally:
        # 1. 파일 감시 서스펜더 먼저 안전하게 중지
        observer.stop()
        observer.join()
        
        # 2. 🚀 [핵심 치트키] 파이썬 메모리가 날아가기 전에 Qdrant 클라이언트를 강제로 먼저 close 시킵니다.
        from src.database import get_qdrant_client
        try:
            qdrant_client = get_qdrant_client()
            qdrant_client.close()
            print("💾 Qdrant 파일 데이터베이스가 안전하게 닫혔습니다.")
        except Exception:
            pass
            
        print("✨ 파이프라인 엔진이 완벽하게 정리되어 종료되었습니다.")

