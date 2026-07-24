---
date created: Monday, May 11th 2026, 10:10:22 am
date modified: Monday, July 6th 2026, 10:19:32 am
status: 출간
post_id: 20260724-wiki-sql-3b40
---

### 🤖 AI 자동 요약 및 인덱싱
-  윈도 함수는 행의 세분성을 유지하면서 계산된 값을 추가하는 SQL 함수로, GROUP BY와 달리 옆에 계산된 값을 추가.
-  윈도 함수는 `PARTITION BY`를 사용하여 데이터를 분할하고, `ORDER BY`를 통해 누적/순위 계산을 수행.

#데이터 #SQL

---

### 본문
# 1. 설명

## 1-1. 개념

윈도 함수(분석함수, 순위함수)
: 행과 행간을 비교, 연산, 정의하는 함수
	- GROUP BY 와 달리 행의 세분성을 유지하면서(결과 행 수 유지) 옆에 계산된 값을 추가.
	- OVER 절 필수.

## 1-2. 기본 구조

```sql
SELECT 함수(컬럼) OVER (
    [PARTITION BY 컬럼] 
    [ORDER BY 컬럼]
    [ROWS/RANGE BETWEEN ...]
) FROM 테이블명;
```


## 1-3. 옵션 조합별 동작 양상

윈도 함수는 `PARTITION BY`로 **그룹**을 나누고, `ORDER BY`로 **누적/순서**를 결정한다.

| **구분**               | **ORDER BY (X)**                               | **ORDER BY (O)**                                           |
| -------------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| **PARTITION BY (X)** | **전체 데이터**를 하나의 범위로 보고 통계치 계산 (전체 합계, 전체 평균 등) | **전체 데이터** 내에서 정렬된 순서대로 **누적 계산** 진행 (누적 합계, 순위 등)         |
| **PARTITION BY (O)** | **파티션별**로 묶어서 통계치 계산 (부서별 합계, 지역별 평균 등)        | **파티션 내**에서 정렬된 순서대로 **누적 계산** 진행 (부서내 급여 순위, 부서내 누적 합계 등) |

① PARTITION (X) / ORDER (X) : 전체 통계
- **특징**: `OVER()` 빈 괄호만 사용. 테이블 전체를 하나의 창(Window)으로 간주
- **예**: `SUM(sal) OVER()` → 전 사원의 급여 총합을 모든 행에 표시.
② PARTITION (O) / ORDER (X) : 그룹별 통계
- **특징**: 특정 컬럼을 기준으로 데이터를 분할하지만, 순서는 따지지 않음.
- **예**: `SUM(sal) OVER(PARTITION BY dept)` → 각 부서별 급여 합계를 해당 부서원 행에 표시.
③ PARTITION (X) / ORDER (O) : 전체 누적/순위
- **특징**: 전체 데이터를 정렬한 후, 첫 행부터 현재 행까지의 범위를 계산함.
- **예**: `SUM(sal) OVER(ORDER BY hire_date)` → 입사일 순으로 전사 급여 누적 합계.
④ PARTITION (O) / ORDER (O) : 그룹별 누적/순위
- **특징**: 파티션별로 데이터를 나누고, 그 안에서 다시 정렬하여 계산함.
- **예**: `RANK() OVER(PARTITION BY dept ORDER BY sal DESC)` → 부서 내에서 급여가 높은 순서대로 순위 부여.


# 2. 종류
```SQL
ROW_NUMBER
PARTITION BY

ROW_NUMBER() OVER (ORDER BY X DESC) AS 'XYZ'

ROW_NUMBER() OVER (PARITITION BY ORDER BY X DESC) AS 'XYZ'
```


LOGICAL_OR
윈도우 함수로 쓰였을 때, 윈도우 프레임에 정의된 어느 행이 TRUE이면 TRUE를 반환. 
만약 모두 FALSE이거나 NULL이면 FALSE 반환.
```sql
LOGICA_OR(exp) OVER (
	[PARTITION BY partition_exp]
	[ORDER BY order_exp]
	[window_frame_clause]
)

-- 실제 쿼리
LOGICAL_OR(exp) OVER  
LOGICAL_OR(action_commit = 'manual_save') OVER (PARTITION BY data_id) AS is_modified
```


# 3. 특징

- **PARTITION BY**는 `GROUP BY`와 비슷하게 공간을 쪼개는 역할임.
    
- **ORDER BY**가 들어가는 순간, 윈도 함수의 계산 범위(Window Frame)는 기본적으로 "맨 처음부터 현재 행까지(Unbounded Preceding to Current Row)"인 **누적(Cumulative)** 방식으로 바뀜.
    
- 순위 함수(`RANK`, `ROW_NUMBER`) 등은 반드시 `ORDER BY`가 동반되어야 의미가 있음.

- `QUALIFY`절로 쓰임.

cf. `WHERE`, `HAVING`, `QUALIFY` clause 

| No. | Clause  | Desc                                                       |     |
| --- | ------- | ---------------------------------------------------------- | --- |
| 1   | WHERE   | Filters base rows before any grouping or window functions. |     |
| 2   | HAVING  | Filters aggregated groups.                                 |     |
| 3   | QUALIFY | Filters rows based on window function results.             |     |

## 4-1. 왜 GROUP BY가 아니라 PARTITION BY일까?

`GROUP BY`와 `PARTITION BY`는 '데이터를 쪼개는 행위'는 같지만 '결과물의 형태'가 완전히 다름.
가장 큰 이유는 "행(Row)을 없애느냐, 유지하느냐"의 차이 때문임.

- GROUP BY (집약): 이름 그대로 여러 행을 하나의 그룹으로 '모아서(Group)' 대표값 하나만 남긺. 결과 행의 수가 줄어듦. (100개 행 → 5개 부서별 요약)

- PARTITION BY (분할): 전체 데이터를 특정 기준에 따라 '칸막이(Partition)'만 쳐서 나눌 뿐임. 계산은 칸막이 안에서 따로 돌지만, 원본 행은 그대로 유지됨.

- 비유하자면:
	
	GROUP BY: 반 학생들을 성별로 모아서 "남학생 평균 키, 여학생 평균 키"라는 두 줄짜리 요약 보고서를 만드는 것.
	
	PARTITION BY: 학생들은 자기 자리에 그대로 앉아 있는데, 각자 책상 위에 "우리 반 전체 평균 키"나 "나의 반 등수"가 적힌 포스트잇을 한 장씩 붙여주는 것.


## 4-2. SQL의 PARTITION BY vs 빅쿼리의 Partitioning

- `빅쿼리의 파티셔닝`은 '저장 방식'의 문제라 아예 층위가 다름.

|**구분**|**윈도 함수의 PARTITION BY**|**빅쿼리(DB)의 Partitioning**|
|---|---|---|
|**성격**|**연산(Query) 도구**|**저장(Storage) 구조**|
|**시점**|쿼리가 실행될 때 (Runtime)|데이터를 테이블에 저장할 때|
|**목적**|특정 그룹별로 분석 계산을 하기 위함|필요한 데이터만 골라 읽어 **비용 절감 및 속도 향상**|
|**비유**|서류함 안의 문서를 **포스트잇으로 분류**하며 읽기|서류함 자체를 **날짜별 서랍으로 나누어 보관**하기|


### 빅쿼리의 파티셔닝 (Physical Partitioning)

빅쿼리에서 "이 테이블은 Date 컬럼으로 파티셔닝 되어 있다"라고 하면, 물리적으로 데이터가 날짜별 창고에 나뉘어 저장된 상태임.

`SELECT * FROM table WHERE date = '2023-10-01'` 이라고 치면, 빅쿼리는 다른 날짜 창고는 쳐다보지도 않고 해당 날짜 창고만 뒤짐.

이건 스캔 비용(돈)과 직결되는 아주 중요한 성능 최적화 기법임.

요약하자면
PARTITION BY라는 이름을 쓴 이유는 행을 합치지 않고(Group) 영역만 나누어(Partition) 계산하기 위해서임.

빅쿼리의 파티셔닝은 쿼리 효율을 위해 데이터를 물리적으로 쪼개 놓는 관리 기법이므로, 분석 함수에서 쓰는 구문과는 성격이 다름.