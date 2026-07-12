---
date created: Sunday, July 12th 2026, 2:50:58 pm
date modified: Sunday, July 12th 2026, 2:51:15 pm
status: 출간
---

### 🤖 AI 자동 요약 및 인덱싱
요약:
- 핵심 콘텐츠 파이프라인(Watchdog, Ollama, 대시보드)은 대부분 구현되었으나, 안정성 검증과 로컬 데이터베이스 락 처리가 필요합니다.
- 남은 가장 중요한 작업은 더미 벡터를 실제 검색으로 대체하는 RAG 기능 구현과 GitHub Actions 기반의 자동 배포 워크플로우 완성입니다.

태그:
#RAG #AI파이프라인 #CI_CD

---

### 본문
코드·디렉터리·로컬 데이터 기준으로 정리하면, 당신 감과 같습니다. **지금 남는 핵심은 GitHub Actions(Quartz 배포)와 진짜 RAG**이고, 나머지는 “구현됨 / 런타임 검증만 남음 / 서류”로 나뉩니다.

---

# 이미 갖춰진 것 (코드·데이터상 OK)

| 항목 | 상태 |
|------|------|
| **Watchdog + `status: 출간`** | `app.py`에 `on_modified` → 파싱 → `status == "출간"` 파이프라인 구현됨. `obsidian_vault` / `quartz_content` 실제 존재. |
| **경로 구조** | `prototype/` 기준 `./obsidian_vault`, `./quartz_content`, `./qdrant_local` 일치. |
| **`client.close()`** | `database.py`(init/upsert), `dashboard.py`(조회)에 close 패턴 있음. |
| **Ollama 모델** | `gemma4:latest` 로컬에 있고 `agent.py`와 일치. API 응답 확인됨. |
| **AI 요약 → Qdrant/블로그** | Qdrant 3건, 요약·태그 정상. `quartz_content`에도 AI 블록 반영됨. |
| **대시보드 라디오** | Streamlit 위젯 변경 시 재실행으로 메뉴별 뷰 전환 가능. |
| **작품명** | 대시보드에 **HarvestFlow** 적용. `prototype/`에 Garden 잔재 없음. |

---

# 아직 준비·검증해야 하는 것

## 🛠️ 1. 백엔드 / 파일시스템

| 체크 | 판정 | 비고 |
|------|------|------|
| Watchdog 데몬 **테스트** | 준비 필요 | 코드는 있음. `prototype/`에서 `app.py` 켠 뒤 vault에 `status: 출간` 저장해 **런타임 스모크**만 하면 됨. `on_created`는 없음(신규 파일은 재저장 필요할 수 있음). |
| 비동기 락 | 부분 완료 / 재검증 | close는 있음. 로컬 path Qdrant는 **대시보드+파이프라인 동시 오픈** 시 여전히 깨질 수 있음. `try/finally`·컨텍스트 매니저 권장. 종료 시 “새 클라이언트 열어 close”는 실질 락 해제에 거의 무의미. |
| 폴더 경로 | 주의 | `prototype/` cwd에서는 OK. `upload_to_github`의 `git add quartz_content/*`·CI는 **레포 루트 기준**이라 경로 불일치 가능. |

## 🤖 2. AI / RAG ← 여기가 본작업

| 체크 | 판정 | 비고 |
|------|------|------|
| Ollama 인스턴스 | 거의 OK | 모델·API는 됨. 제출/데모 직전에 백그라운드 기동만 재확인. |
| 임베딩·RAG | **미구현** | `save_to_vector_db`가 `np.random` **더미 벡터**. 의미 검색 불가. 대시보드 “RAG”는 **목록 조회**뿐, query/retrieve 없음. → **실제 임베딩 + 검색 UI/함수**가 남은 핵심. |
| 요약 퀄리티 | 사실상 OK | 기존 적재분은 정상. 파이프라인 E2E 한 번만 더 돌리면 충분. |

## 🌐 3. 배포 / UI ← CI/CD가 본작업

| 체크 | 판정 | 비고 |
|------|------|------|
| 대시보드 리프레시 | 부분 | 라디오는 OK. 파이프라인 신규 적재 **자동 갱신**은 없음(`st.rerun`/폴링 없음). 체크리스트 “실시간”이면 보강 후보. |
| 최종 승인 → BLOG_DIR | 없음 | `status: 출간`이면 **바로** BLOG_DIR 복사·(시도) git push. 대시보드 승인 게이트 없음. |
| GitHub Actions | **미완** | `deploy.yml`은 있으나 `package.json` 비어 있음, Quartz 프로젝트/`content` 없음, “Setup Node”가 `configure-pages`로 잘못됨, `quartz_content`가 `prototype/` 아래. **워크플로·Quartz 스캐폴드·콘텐츠 경로 정렬**이 필요. |

## 📝 4. 제출 서류

| 체크        | 판정         | 비고                                                                      |
| --------- | ---------- | ----------------------------------------------------------------------- |
| 작품명 일괄 교체 | 대시보드만 OK   | `README.md` 비어 있음, 패키지명 `obsidian-ai-pipeline`. 제출 문서·팀명 문구는 레포 밖일 가능성. |
| 글자 수      | 레포에서 확인 불가 | 개발목적/소개/기대효과 텍스트가 코드베이스에 없음 → 제출 폼 기준으로 직접 카운트.                         |

---

# 우선순위 (당신 판단과 맞춤)

1. **RAG**: 더미 벡터 → 실제 임베딩(예: Ollama embed / FastEmbed) + Qdrant `search` + 대시보드 검색.
2. **GitHub Actions + Quartz**: Quartz 설치·`content` 경로·`npm ci` 가능한 `package.json`·워크플로 Node 셋업 수정·`prototype/quartz_content` ↔ 배포 입력 경로 통일.
3. **짧은 스모크**: Watchdog E2E, 대시보드↔파이프라인 동시 실행 시 Qdrant lock, Ollama 기동.
4. **서류**: HarvestFlow/팀명 잔여 문서, 글자 수.

원하면 다음으로 RAG부터 넣을지, Actions/Quartz부터 맞출지 정해 주면 그 순서대로 패치 들어가면 됩니다.