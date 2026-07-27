---
status: 출간
date created: Tuesday, April 14th 2026, 6:23:00 pm
date modified: Monday, July 27th 2026, 9:34:24 pm
post_id: 20260727-wiki-airflow-core-35f1
---

### 🤖 AI 자동 요약 및 인덱싱
## 요약 

- 이 글은 Airflow 환경변수 조정을 통한 GCE 부하 최적화 방법에 대한 설명입니다.  
- 특히, `load_examples=False`, `parallelism` 등의 설정 변수를 통해 Airflow의 성능을 개선할 수 있습니다. 

## 태그

#데이터 #생산성

---

### 본문
# 배경

Airflow 환경변수를 조절해서 GCE 부하를 낮추고자 한다.
이와 관련해 공식문서 기반으로 각 환경변수가 인프라에 영향을 미치는지 아닌지 사전 조사한 내용이다.
- Airflow 버전:  `2.3.3`

# 튜닝 포인트

- **`load_examples=False`**: 예제 DAG들이 차지하는 파싱 CPU와 DB 용량을 아껴야 해.
- **`parallelism=12` 이하**: CPU 코어 대비 너무 많은 작업이 몰리지 않게 제한해.
- **`sql_alchemy_pool_size=5`**: DB 커넥션이 메모리를 갉아먹지 않게 작게 유지해.

# 영향 O

| 설정 항목                                | 한 줄 설명                                |
| ------------------------------------ | ------------------------------------- |
| compress_serialized_dags             | DB에 저장되는 DAG 정보 압축 여부 (메모리 절약)        |
| dag_discovery_safe_mode              | 파일 내 DAG 단어 포함 여부 검사 (파싱 부하 관련)       |
| dag_file_processor_timeout           | DAG 파일 하나를 파싱할 때 허용되는 최대 시간           |
| dagbag_import_timeout                | DAG 파일을 읽어올 때 허용되는 최대 시간 (CPU 점유)     |
| default_pool_task_slot_count         | 기본 풀(Default Pool)의 최대 슬롯 수           |
| enable_xcom_pickling                 | XCom 데이터 전달 시 Pickle 사용 여부 (보안/용량 관련) |
| execute_tasks_new_python_interpreter | 작업을 별도 파이썬 프로세스로 실행 (메모리 부하 큼)        |
| executor                             | 작업을 어떤 방식으로 실행할지 결정 (Local, Celery 등) |
| lazy_load_plugins                    | 필요할 때만 플러그인을 로드 (메모리 절약)              |
| load_examples                        | 예제 DAG 로드 여부 (무조건 False 권장)           |
| max_active_runs_per_dag              | DAG 하나당 동시에 돌 수 있는 최대 실행(Run) 수       |
| max_active_tasks_per_dag             | DAG 하나당 동시에 실행될 수 있는 최대 작업(Task) 수    |
| max_map_length                       | Dynamic Task Mapping으로 생성 가능한 최대 작업 수 |
| min_serialized_dag_fetch_interval    | DB에서 직렬화된 DAG를 다시 가져오는 주기             |
| min_serialized_dag_update_interval   | DB에 DAG 정보를 업데이트하는 주기                 |
| parallelism                          | 에어플로 전체에서 동시에 실행될 수 있는 총 작업 수         |
# 영향 O(Deprecated, but 중요)

| 설정 항목                    | 한 줄 설명                                   |
| ------------------------ | ---------------------------------------- |
| dag_concurrency          | (현 max_active_tasks_per_dag) 동시 실행 작업 수  |
| logging_level            | 로그 기록 상세도  <br>(INFO/DEBUG 등, 디스크 IO 영향) |
| sql_alchemy_max_overflow | DB 풀 초과 시  <br>허용되는 추가 커넥션 수             |
| sql_alchemy_pool_size    | DB 연결 유지를 위한  <br>풀 크기 (메모리/DB 부하)       |
# 전체

| **설정 항목**                                | **한 줄 설명**                            | **인프라 영향** |
| ---------------------------------------- | ------------------------------------- | ---------- |
| **check_slas**                           | 작업 완료 시간(SLA) 미준수 체크 여부               | **X**      |
| **compress_serialized_dags**             | DB에 저장되는 DAG 정보 압축 여부 (메모리 절약)        | **O**      |
| **dag_discovery_safe_mode**              | 파일 내 `DAG` 단어 포함 여부 검사 (파싱 부하 관련)     | **O**      |
| **dag_file_processor_timeout**           | DAG 파일 하나를 파싱할 때 허용되는 최대 시간           | **O**      |
| **dag_ignore_file_syntax**               | `.airflowignore` 파일의 구문 형식 지정         | **X**      |
| **dag_run_conf_overrides_params**        | 실행 시 전달된 config로 파라미터 덮어쓰기 허용         | **X**      |
| **dagbag_import_error_traceback_depth**  | 임포트 에러 발생 시 추적 깊이 설정                  | **X**      |
| **dagbag_import_error_tracebacks**       | 임포트 에러 추적 정보 표시 여부                    | **X**      |
| **dagbag_import_timeout**                | DAG 파일을 읽어올 때 허용되는 최대 시간 (CPU 점유)     | **O**      |
| **dags_are_paused_at_creation**          | 새로운 DAG 생성 시 기본 일시정지 상태 여부            | **X**      |
| **dags_folder**                          | DAG 파일이 위치한 실제 경로                     | **X**      |
| **default_impersonation**                | 작업을 실행할 Unix 유저 지정                    | **X**      |
| **default_pool_task_slot_count**         | 기본 풀(Default Pool)의 최대 슬롯 수           | **O**      |
| **default_task_execution_timeout**       | 개별 작업의 기본 실행 제한 시간                    | **X**      |
| **default_task_retries**                 | 작업 실패 시 기본 재시도 횟수                     | **X**      |
| **default_task_weight_rule**             | 작업 우선순위 결정 규칙                         | **X**      |
| **default_timezone**                     | 에어플로 시스템 타임존 설정                       | **X**      |
| **donot_pickle**                         | 파이썬 객체 직렬화(Pickle) 사용 안 함 여부          | **X**      |
| **enable_xcom_pickling**                 | XCom 데이터 전달 시 Pickle 사용 여부 (보안/용량 관련) | **O**      |
| **execute_tasks_new_python_interpreter** | 작업을 별도 파이썬 프로세스로 실행 (메모리 부하 큼)        | **O**      |
| **executor**                             | 작업을 어떤 방식으로 실행할지 결정 (Local, Celery 등) | **O**      |
| **fernet_key**                           | DB 내 암호화된 데이터 복호화를 위한 키               | **X**      |
| **hide_sensitive_var_conn_fields**       | UI에서 민감 정보(비번 등) 숨김 여부                | **X**      |
| **hostname_callable**                    | 서버의 호스트네임을 가져오는 방식                    | **X**      |
| **killed_task_cleanup_time**             | 작업 종료 시 정리 프로세스 대기 시간                 | **X**      |
| **lazy_discover_providers**              | 필요할 때만 프로바이더 정보를 로드 (시작 속도 최적화)       | **X**      |
| **lazy_load_plugins**                    | 필요할 때만 플러그인을 로드 (메모리 절약)              | **O**      |
| **load_examples**                        | 예제 DAG 로드 여부 (**무조건 False 권장**)       | **O**      |
| **max_active_runs_per_dag**              | DAG 하나당 동시에 돌 수 있는 최대 실행(Run) 수       | **O**      |
| **max_active_tasks_per_dag**             | DAG 하나당 동시에 실행될 수 있는 최대 작업(Task) 수    | **O**      |
| **max_map_length**                       | Dynamic Task Mapping으로 생성 가능한 최대 작업 수 | **O**      |
| **max_num_rendered_ti_fields_per_task**  | 렌더링된 필드 저장 개수 제한                      | **X**      |
| **min_serialized_dag_fetch_interval**    | DB에서 직렬화된 DAG를 다시 가져오는 주기             | **O**      |
| **min_serialized_dag_update_interval**   | DB에 DAG 정보를 업데이트하는 주기                 | **O**      |
| **parallelism**                          | **에어플로 전체에서 동시에 실행될 수 있는 총 작업 수**     | **O**      |
| **plugins_folder**                       | 플러그인 파일이 위치한 경로                       | **X**      |
| **security**                             | 보안 관련 설정                              | **X**      |
| **sensitive_var_conn_names**             | 민감 정보로 간주할 변수명 리스트                    | **X**      |
| **task_runner**                          | 작업을 실행하는 내부 모듈 방식                     | **X**      |
| **unit_test_mode**                       | 유닛 테스트 모드 활성화 여부                      | **X**      |
| **xcom_backend**                         | XCom 데이터를 저장할 커스텀 클래스 지정              | **X**      |