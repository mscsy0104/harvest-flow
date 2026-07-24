---
status: 출간
date created: Wednesday, July 8th 2026, 5:46:59 pm
date modified: Wednesday, July 8th 2026, 5:57:43 pm
---

### 🤖 AI 자동 요약 및 인덱싱
- 본문은 Redis 없애기, Trigger Dag 없애기 등의 작업을 통해 구조를 간결하게 만들고 Airflow 이관에 유리한 모듈 분담과 데이터 흐름 구조를 제시합니다.
-  모듈별로 책임을 분리하고 SQL 문장을 분리하여 코드의 가독성과 유지보수성을 높이고, Airflow 이관 시에도 활용 가능한 구조를 제공합니다.

#태그: #데이터 #Airflow

---

### 본문
redis 없애기
trigger dag 없애기
trigger 없애기
trigger - scheduler - processor 형태인 이유는 redis를 이용하기 위해서로 보임.


profile.yml -> credentials/gcp_middleware.json, .env, config.py

de-data-sync-checker -> mysql-bq-sync-checker

redis -> config.yml(DB connection, Table list)

query들은 따로 폴더에 모아두기
sql 폴더에도 있고
type01_processor.py에도 있음.

calculate.py
1.
calc_prj_data
calc_base_data
`process_prj_data`는 특정 날짜 필터가 필요하고  
`process_base_data`는 특정 날짜 필터가 필요없다.

2.
시작 일자와 종료 일자 사이에 날짜를 쪼개서 date_list를 만듦. 왜?
-> 확인해봤는데 안 해도 될 듯. 
이유: 실질적인 스케줄링은 airflow trigger dag에서 하고 있는데 날짜 1개이고(kst니까 서버에서 설정할 땐 고려 필요),
날짜 전달은 restapi_trigger.py가 하는데 redis로 start_date, end_date으로 큐 저장한다. 결과적으로
airflow trigger dag으로 하루하루 세팅하도록 했기 때문에 매번 1개짜리 리스트가 생성되는 것임.
따라서 필요 없음.


```
cron: 스케줄링
main.py: Main
logger.py: 로거 설정
query/…: 계산에 필요한 쿼리
datastore.py: bigquery, mysql client
extractor.py: bigquery, mysql 조회 실행 및 결과 데이터 반환
calculate.py: extractor 결과 비교, 매칭 여부 반환
alert.py: 결과 미매칭일 경우 구글 챗 webhook 발송
```


구조를 아주 직관적이고 역할 분담이 명확하게 잘 짜셨습니다! 모듈별로 책임을 분리해 두셔서 나중에 코드가 커지거나 Airflow로 이관할 때 리팩토링하기 매우 유리한 구조입니다.

이 구조에서 코드의 가독성, 유지보수성, 그리고 나중의 확장성(Airflow)을 위해 한 단계 더 업그레이드할 수 있는 보완점과 팁을 몇 가지 정리해 드릴게요.

# 🛠️ 모듈별 보완점 및 네이밍 팁

## 1. `select.py` ➔ `repository.py` 또는 `extractor.py` (네이밍 보완)

- **이유:** `select`는 SQL 예약어(Keyword)이기도 하고, Python 내부 모듈 중에도 동명의 `select` 모듈이 존재하여 나중에 `import select` 할 때 충돌하거나 헷갈릴 위험이 있습니다.
    
- **추천:** 데이터를 조회해서 가져오는 역할이므로 **`extractor.py`**(추출기) 또는 데이터 접근 계층을 뜻하는 `repository.py`로 이름을 바꾸는 것이 더 안전하고 직관적입니다.
    

## 2. `query/` 폴더 활용 팁 (SQL 분리)

- Python 코드 내부에 긴 SQL 문자열을 욱여넣으면 코드가 지저분해집니다. `query/` 폴더 아래에 `mysql_count.sql`, `bigquery_count.sql` 처럼 **순수 SQL 파일**로 저장해 두고, `extractor.py`에서 이 파일을 읽어서(`open().read()`) 실행하게 하세요.
    
- 이렇게 하면 SQL 문법 하이라이팅도 잘 되고, 나중에 쿼리만 수정할 때 Python 코드를 건드릴 필요가 없어집니다.
    

## 3. `datastore.py` ➔ Context Manager(with문) 대응

- DB와 BigQuery 클라이언트는 커넥션을 열었으면 잘 닫아주는 것이 중요합니다. `datastore.py`에서 클라이언트를 생성할 때 Python의 `with` 문(Context Manager)을 지원하도록 클래스를 설계하거나, `finally` 절에서 확실히 `close()`되도록 구조를 잡아주세요.
    

# 🔄 전체적인 데이터 흐름 (Data Flow) 추천

각 모듈이 데이터를 주고받을 때 아래와 같은 흐름으로 연결되면 가장 깔끔합니다.

Plaintext

```
[main.py] 
   │
   ├──> [logger.py] 로깅 시작
   │
   ├──> [extractor.py] (with datastore.py 클라이언트)
   │       └──> query/ 에서 SQL 읽어서 조회 실행 ➔ 결과 데이터 반환
   │
   ├──> [calculate.py] 결과 데이터를 넘겨받아 비교 ➔ 매칭 여부(True/False) 반환
   │
   └──> [alert.py] 결과가 False(미매칭)인 경우 구글 챗 Webhook 발송
```

# 🚀 Airflow 이관을 염두에 둔 강력한 보완 팁

나중에 이 코드를 Airflow DAG로 옮길 때, 지금 짠 구조를 **그대로 재사용**하려면 `main.py`와 `calculate.py`를 다음과 같이 설계해 두는 것이 좋습니다.

## 1. `main.py`에 테이블 이름을 인자(Argument)로 받게 만들기

크론탭에서 실행할 때 전체 테이블을 다 돌 수도 있지만, 나중에 Airflow로 가면 "테이블 1개당 태스크 1개"로 쪼개서 실행하는 것이 모니터링하기 좋습니다.

이를 위해 `main.py`가 특정 테이블 이름이나 태스크 ID를 파라미터로 받아서 실행할 수 있게 `sys.argv`나 `argparse`를 붙여두세요.

Bash

```
# 크론탭에서는 전체 실행
python3 main.py --all

# 나중에 Airflow에서는 테이블별로 쪼개서 실행 가능
python3 main.py --task metadata_sync_check
```

## 2. `calculate.py`는 순수 함수(Pure Function)로 만들기

`calculate.py` 내부에서는 DB 접속이나 구글 챗 알림 같은 부수 효과(Side Effect)를 절대 일으키지 마세요. 오직 "MySQL 개수와 BigQuery 개수를 입력받아 비교 결과만 리턴"하는 계산 공식만 넣어두어야 합니다.

그래야 나중에 Airflow로 이관했을 때 코드를 수정하지 않고 테스트(Unit Test)하기도 편하고 오퍼레이터에 이식하기도 좋습니다.

# 요약

- `select.py`는 파일명 충돌 방지를 위해 `extractor.py`나 `repository.py`로 변경 추천.
    
- `query/` 폴더에는 `.sql` 파일 형태로 쿼리를 격리하기.
    
- 현재 구조가 워낙 탄탄해서 이 정도 디테일만 잡아주시면 단일 서버 크론 배치로도 완벽하고, 추후 Airflow 이관도 몇 시간 만에 끝낼 수 있는 훌륭한 아키텍처가 됩니다!