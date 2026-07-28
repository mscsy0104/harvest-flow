---
status: 출간
date created: Tuesday, July 21st 2026, 5:41:16 pm
date modified: Tuesday, July 28th 2026, 11:40:06 pm
post_id: 20260728-wiki-airflow-dag-ca49
---

### 🤖 AI 자동 요약 및 인덱싱
- Airflow DAG 이름은 데이터 처리 방식에 따라 다르게 구성되어 운영 사고를 줄일 수 있습니다. 
-  DAG 이름 패턴과 실제 예시, 그리고 각 작업의 Task 구성 팁을 통해 데이터 처리 과정을 명확하게 이해할 수 있습니다.

#데이터 #DAG

---

### 본문
# 배경
Airflow에서 DB 혹은 Bigquery에 데이터 처리할 때 다양한 경우가 있다. 
truncate, insert, merge하거나 merge만 하거나 계산을 하거나, 각각 어떤 식의 dag 이름이 좋을지 알아보자.


# 설명

데이터 파이프라인의 작업 방식(전략)에 따라 DAG 이름을 다르게 가져가면, Airflow UI만 보고도 "이 작업은 데이터를 통째로 갈아엎는구나", "이 작업은 누적 업데이트구나"를 바로 파악할 수 있어 운영 사고를 크게 줄일 수 있음.
작업 방식별로 실무에서 가장 많이 쓰는 DAG 네이밍 가이드와 내부 Task 구성 예시를 정리해보자.

------------------------------
# 1. Truncate + Insert (전체 재작성)
기존 데이터를 모두 지우고 새로 적재하는 방식임. 데이터 볼륨이 작거나, 매번 전체 스냅샷을 보관해야 할 때 사용함. 'Insert'보다는 'Overwrite'나 'Full'이라는 키워드를 매칭하는 것이 직관적임.

* 추천 DAG 이름 패턴: `[Source]_to_[Target]_[테이블명]_overwrite`
* 실제 예시: `dw_to_dm_user_profile_overwrite`
* Task 구성 팁: `truncate_target_table` → `insert_from_source`

# 2. Merge (증분 업데이트 / Upsert)
기존에 있는 데이터는 업데이트(Update)하고, 없는 데이터는 삽입(Insert)하는 방식임. 대용량 로그나 날짜별 누적 데이터를 다룰 때 사용함. 'Upsert' 또는 'Merge'를 붙여줌. [1, 2]

* 추천 DAG 이름 패턴: `[Source]_to_[Target]_[테이블명]_upsert (또는 _merge)`
* 실제 예시: `dw_to_dm_order_hist_upsert`
* Task 구성 팁: BigQuery의 경우 SQL 내에서 MERGE INTO... 문을 사용하므로, Task ID는 merge_order_hist 형태로 단순화할 수 있음.

# 3. 계산 및 지표 추출 (Aggregations / Transformations)
단순히 데이터를 옮기는 게 아니라, 여러 테이블을 조인하고 복잡한 수식을 적용해 통계/지표를 만들어내는 작업임. 이때는 'Agg'(Aggregation)나 'Summary', 'Stats' 같은 목적성 키워드를 붙여줌.

* 추천 DAG 이름 패턴: `[Dataset]_[지표명]_agg (또는 _summary)`
* 실제 예시: `dm_sales_performance_agg`
* Task 구성 팁: 복잡한 계산은 보통 단계별로 일어나므로 Task ID를 `calc_daily_revenue` →  `calc_conversion_rate` 형태로 쪼개면 모니터링하기 좋음.

------------------------------
# 💡 한눈에 보는 요약 가이드

| 작업 성격     | DAG 접미사 (Suffix) 추천 | 예시 (DW → DM 이동 시)           |
| --------- | ------------------- | --------------------------- |
| 비우고 새로 넣기 | _overwrite 또는 _full | dw_to_dm_customer_overwrite |
| 업데이트 + 삽입 | _upsert 또는 _merge   | dw_to_dm_transaction_upsert |
| 복잡한 통계/계산 | _agg 또는 _summary    | dw_to_dm_monthly_kpi_agg    |