---
date created: Friday, July 17th 2026, 3:33:37 pm
date modified: Friday, July 17th 2026, 3:45:14 pm
status: 출간
post_id: 20260731-wiki-012b
---

### 🤖 AI 자동 요약 및 인덱싱
- cron + 배치 작업은 자동 실행을 위한 방법으로, Airflow와 함께 사용하여 DAG를 수동/자동적으로 실행할 수 있습니다. 핵심 키워드는 #데이터 #생산성 입니다.
#태그1 #데이터 #Airflow

---

### 본문
# cron + 배치 작업

- cron 주석 처리하고 추후 수동 실행


# Airflow

과거 DAG 실행해야 하므로 순차적으로 돌도록 제어 필요.

---
## 자동 실행
- `catchup=True`(default지만 확인 필요)
	- 하지만 주의할 점, 이 상태로 pause했다가 다시 unpause하면 한 번에 돌면서 에러 메시지 보낼 가능성 있으므로, 다음 처리가 필요하다.
- `max_active_runs=1` 
	- 밀린 작업이 아무리 많아도 이전 작업이 완전히 끝난 후에야 다음 과거 작업이 순차적으로 실행
- `depends_on_past = True` 
	- 특정 Task가 바로 직전 스케줄의 동일한 Task가 성공했을 때만 실행되도록 강제됨. 순서대로 데이터가 쌓여야 정합성이 맞는 작업에 필수적임.
- Pool을 이용한 슬롯 제한: 브라우저에서 `Admin -> Pools` 설정, DAG에서 `pool='제한된_풀_이름'`
	- 여러 DAG에 걸쳐 시스템 자원을 많이 먹는 무거운 Task들이 있다면, Airflow UI의 `Admin -> Pools`에서 제한된 슬롯(예: 2개)을 가진 Pool을 생성합니다. 그리고 부하가 큰 Task들을 해당 Pool에 할당(`pool='제한된_풀_이름'`)하면, 전체 Airflow 환경에서 해당 작업들이 설정된 슬롯 수만큼만 동시에 실행되도록 통제할 수 있음.
```python
# max_active_runs
dag = DAG(
    'my_dag',
    catchup=True,
    max_active_runs=1, # 한 번에 하나의 DAG만 실행
    schedule_interval='@daily'
)

# depends_on_past
default_args = {
    'depends_on_past': True, # 이전 스케줄의 해당 태스크가 성공해야만 실행
}
```

## 수동 실행

CLI를 이용해 수동으로 처리하는 경우 (Backfill)
작업자가 직접 눈으로 보면서 원하는 기간만 골라서 돌릴 수 있어 가장 안전하고 통제력이 높은 방식. 하지만 스케줄러와의 충돌을 막기 위해 순서를 반드시 지켜야 함.

- **폭주 차단:** 먼저 DAG 코드에 `catchup=False`를 명시적으로 추가하고 배포.
    
- **스케줄러 재개:** DAG를 Unpause. 이제 스케줄러는 과거 밀린 작업은 무시하고, 다가오는 새로운 정규 스케줄만 정상적으로 실행.
    
- **CLI로 과거 작업 실행:** 터미널에 접속해 `backfill` 명령어를 사용하여 정전으로 누락된 구간만 명시적으로 실행.

```bash
# 예시: 7월 24일부터 25일까지의 작업을 순차적으로 실행
airflow dags backfill -s 2026-07-24 -e 2026-07-25 my_dag_id
```


## Airflow catchup 자동/수동 요약

- 스케줄러가 알아서 천천히 따라잡게 하려면 코드에 `max_active_runs=1`을 추가.
- 내가 원할 때 수동으로 과거 구간만 돌리려면 `catchup=False`로 스케줄러를 묶어둔 뒤 CLI의 `backfill` 명령어를 사용하기.