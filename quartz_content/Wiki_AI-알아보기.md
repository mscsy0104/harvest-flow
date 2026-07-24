---
date created: Friday, April 17th 2026, 8:39:50 pm
date modified: Friday, July 24th 2026, 11:08:43 pm
status: 출간
post_id: 20260724-wiki-ai-b61c
---

### 🤖 AI 자동 요약 및 인덱싱
- Langchain LLM RAG 차이를 설명한 글입니다. 
- LLM, RAG, LangChain의 역할과 특징을 비교 분석합니다.

#데이터 #프레임워크 #LLM

---

### 본문
<!-- HF_REVIEW_CHECKLIST_START -->
## 검수 체크리스트
- [ ] 메시지와 제목이 일치한다
- [ ] 사실/수치/링크를 재확인했다
- [ ] TODO, TBD, placeholder 텍스트가 없다
- [ ] 문단/헤더 구조가 읽기 쉽게 정리되어 있다
<!-- HF_REVIEW_CHECKLIST_END -->

2025년 12월 26일 Langchain LLM RAG 차이
    
LLM(대규모 언어 모델)은 학습된 데이터로 답변하는 '뇌',

RAG는 외부 데이터를 검색해 LLM에 제공하는 '지식 탐색 기법',

랭체인(LangChain)은 이 둘을 연결하고 제어하는 '프레임워크'임.

**LLM은 지식의 한계를, RAG는 최신/전문 정보를, 랭체인은 구현 유연성을 해결함**.

| 구분  | LLM               | RAG              | LangChain           |
| --- | ----------------- | ---------------- | ------------------- |
| 역할  | 내용 생성 및 이해 (뇌)    | 외부 정보 검색 (검색/보강) | 애플리케이션 연결 (프레임워크)   |
| 핵심  | 모델 자체의 지식 (Param) | 최신성, 전문성 확보      | 유연한 워크플로우 구현        |
| 관점  | 모델 (Model)        | 기법 (Technique)   | 도구 (Tool/Framework) |

- [**LLM (Large Language Model)](https://www.google.com/search?q=LLM+%28Large+Language+Model%29&oq=langchain+llm+rag+%EC%B0%A8%EC%9D%B4&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQABgeMggIAhAAGAgYHjIICAMQABgIGB4yCAgEEAAYCBgeMggIBRAAGAgYHjIICAYQABgIGB4yCAgHEAAYCBgeMggICBAAGAgYHjIICAkQABgIGB7SAQg2MDU1ajBqN6gCALACAA&sourceid=chrome&ie=UTF-8&mstk=AUtExfB8836BTuZ2Mm77DRGHtEvd1Obuf7uX5btprj6KDgAdEzXExAVIftay2CJ4ANW1XpnmStt3FW0LXgdK4p8amf5SXVOyxCj6AYHB0531WmRpL_76cfbj-TiERLA_Dqkn3TSnQluSjBKWVR9XA5L5qahNC21RmDJsIWal4zhn_pV0Nasdvo8JrscUBuPE4MQP9KhI&csui=3&ved=2ahUKEwi6zqfVhNqRAxWMslYBHbWdIokQgK4QegQIAhAB) (두뇌)**
	
	**:** GPT-4, Claude 같은 모델 자체. 학습된 데이터 내에서 문맥을 이해하고 문장을 생성함.
	
- [**RAG (Retrieval-Augmented Generation)](https://www.google.com/search?q=RAG+%28Retrieval-Augmented+Generation%29&oq=langchain+llm+rag+%EC%B0%A8%EC%9D%B4&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQABgeMggIAhAAGAgYHjIICAMQABgIGB4yCAgEEAAYCBgeMggIBRAAGAgYHjIICAYQABgIGB4yCAgHEAAYCBgeMggICBAAGAgYHjIICAkQABgIGB7SAQg2MDU1ajBqN6gCALACAA&sourceid=chrome&ie=UTF-8&mstk=AUtExfB8836BTuZ2Mm77DRGHtEvd1Obuf7uX5btprj6KDgAdEzXExAVIftay2CJ4ANW1XpnmStt3FW0LXgdK4p8amf5SXVOyxCj6AYHB0531WmRpL_76cfbj-TiERLA_Dqkn3TSnQluSjBKWVR9XA5L5qahNC21RmDJsIWal4zhn_pV0Nasdvo8JrscUBuPE4MQP9KhI&csui=3&ved=2ahUKEwi6zqfVhNqRAxWMslYBHbWdIokQgK4QegQIAhAD) (지식 기반)**
	
	**:** 외부 도큐먼트(DB)에서 관련 정보를 검색하여 LLM에 프롬프트로 전달, 할루시네이션(거짓 답변)을 줄이고 최신 정보 반영.
	
	- 요약: 외부 지식을 가져와 **LLM**에게 주는 행동
- [**LangChain (프레임워크)](https://www.google.com/search?q=LangChain+%28%ED%94%84%EB%A0%88%EC%9E%84%EC%9B%8C%ED%81%AC%29&oq=langchain+llm+rag+%EC%B0%A8%EC%9D%B4&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQABgeMggIAhAAGAgYHjIICAMQABgIGB4yCAgEEAAYCBgeMggIBRAAGAgYHjIICAYQABgIGB4yCAgHEAAYCBgeMggICBAAGAgYHjIICAkQABgIGB7SAQg2MDU1ajBqN6gCALACAA&sourceid=chrome&ie=UTF-8&mstk=AUtExfB8836BTuZ2Mm77DRGHtEvd1Obuf7uX5btprj6KDgAdEzXExAVIftay2CJ4ANW1XpnmStt3FW0LXgdK4p8amf5SXVOyxCj6AYHB0531WmRpL_76cfbj-TiERLA_Dqkn3TSnQluSjBKWVR9XA5L5qahNC21RmDJsIWal4zhn_pV0Nasdvo8JrscUBuPE4MQP9KhI&csui=3&ved=2ahUKEwi6zqfVhNqRAxWMslYBHbWdIokQgK4QegQIAhAF) (연결 도구)**
	
	**:** LLM, 데이터 소스, 프롬프트, 도구를 연결하여 RAG 파이프라인(검색-생성)을 효율적으로 구성하게 해주는 개발 도구
	
	- 요약: **RAG**를 구현하기 위해 **LLM**과 데이터베이스를 이어주는 파이프라인을 만드는 도구