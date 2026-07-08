---
date created: Friday, June 19th 2026, 1:37:10 pm
date modified: Friday, June 19th 2026, 3:30:29 pm
status: 출간
---

### 🤖 AI 자동 요약 및 인덱싱
요약:
대규모 Airflow 메타데이터 덤프 파일(dump)을 GCE $\rightarrow$ 로컬 PC $\rightarrow$ 온프레미스 환경으로 안전하게 다단계 전송하는 과정을 수행했습니다. 타겟 환경에서는 Docker 기반의 PostgreSQL 컨테이너를 재구성하고, 복원 과정에서 발생한 세션 충돌(`pg_terminate_backend`), 트랜잭션 블록 오류 등 데이터베이스 레벨의 장애를 해결했습니다. 나아가 Airflow Web UI의 정상 작동을 위해 마이그레이션 잡 수동 실행 및 가장 중요하게는 Python Pickle Protocol 버전 불일치(3.7 $\rightarrow$ 3.8) 문제를 Helm 차트와 이미지 태그 수정으로 근본적으로 해결하여, 데이터 무결성을 확보하고 운영 환경을 성공적으로 복구했습니다.

태그:
Airflow, PostgreSQL, Docker, Kubernetes (K3s), Data Migration, DevOps, Troubleshooting, GCE, Helm, Python Compatibility

---

### 본문
# dump 연동과정

![[TS_K3s-dump-연동-1781843851009.webp]]

에러 뜨기 시작.
![[TS_K3s-dump-연동-1781843909943.webp]]


terminating 했으나 해결이 안 됨. session이 실행 중이어서 그랬음.
![[TS_K3s-dump-연동-1781844051883.webp]]



연결된 DB를 내려야했음. 어차피 테스트 데이터만 쌓였기 때문에 바로 `DROP`해버림.
![[TS_K3s-dump-연동-1781844118529.webp]]

따라서 이 부분은 해결됨.

---

그런데 기존 계정 'admin/admin'으로는 접속이 안 됐고, DB 관련한 계정 'airflow/airflow'로는 접속이 됐으나, 일부 DAG만 실행가능한 상태였음.

확인해보니 Helm Chart `1.7.0`이 Python 3.7을 자동으로 쓰기 때문에, 레거시의 Python 3.8과 맞지 않아 로딩이 안 됐던 거였다. `ValueError: unsupported pickle protocol: 5`.


---

# Airflow k3s 트러블슈팅 (2026-06-19)

---

## 1. postgres:13 컨테이너 접속 불가 (psql 연결 오류)

### 문제
- Docker 컨테이너 `airflow-host-postgres` (postgres:13) 에 psql 접속 시 연결 실패

### 원인 조사
```bash
sudo docker ps -a   # 컨테이너 이름·포트 확인
sudo docker inspect airflow-host-postgres --format '{{json .Config.Env}}'  # 환경변수 확인
sudo docker exec airflow-host-postgres psql -U airflow -d airflow_compat -c "\l"  # 접속 시도
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "\l"  # 기본 DB로 접속
```

### 원인
- 컨테이너 환경변수 `POSTGRES_DB=airflow_compat` 으로 설정되어 있으나, 해당 DB가 실제로 존재하지 않음
- 컨테이너 기동 시 데이터 디렉토리가 이미 존재해 초기화 스크립트가 실행되지 않아 발생
- 실제 존재하는 DB: `airflow_legacy`, `airflow_legacy_test`, `postgres`

### 해결
- 접속 시 `-d` 옵션으로 존재하는 DB 명시
```bash
sudo docker exec -it airflow-host-postgres psql -U airflow -d postgres
# Username: airflow / Password: airflow
```

---

## 2. airflow-legacy DB dump 복원 중 세션 충돌

### 문제
- `DROP DATABASE airflow_legacy` 실행 시 다른 세션이 접속 중이라 실패
```
ERROR: database "airflow_legacy" is being accessed by other users
DETAIL: There are 12 other sessions using the database.
```

### 원인 조사
```bash
# 세션 강제 종료 시도
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE datname = 'airflow_legacy' AND pid <> pg_backend_pid();"
```

### 원인
- k3s airflow pod들이 `airflow_legacy` DB에 지속적으로 재연결하면서 세션 종료 후에도 새 세션이 생성됨

### 해결
- airflow 네임스페이스 pod 전체 스케일 다운 후 세션 종료 및 DROP 실행
```bash
kubectl scale deployment --all -n airflow --replicas=0
kubectl scale deployment --all -n airflow-compat-test --replicas=0

sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE datname = 'airflow_legacy' AND pid <> pg_backend_pid();"

sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "DROP DATABASE airflow_legacy;"
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "CREATE DATABASE airflow_legacy OWNER airflow;"
```

---

## 3. DROP DATABASE 트랜잭션 블록 오류

### 문제
```
ERROR: DROP DATABASE cannot run inside a transaction block
```

### 원인 조사
```bash
# 한 번에 두 문장을 -c 옵션에 넣어 실행
psql -c "DROP DATABASE airflow_legacy; CREATE DATABASE airflow_legacy OWNER airflow;"
```

### 원인
- psql `-c` 옵션에 세미콜론으로 구분된 다중 구문을 넣으면 트랜잭션 블록으로 묶여 실행됨
- `DROP DATABASE`는 트랜잭션 블록 내에서 실행 불가

### 해결
- 명령을 분리해 각각 실행
```bash
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "DROP DATABASE airflow_legacy;"
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "CREATE DATABASE airflow_legacy OWNER airflow;"
```

---

## 4. dump 복원 후 airflow pod init 컨테이너 무한 대기

### 문제
- pod 재기동 후 `wait-for-airflow-migrations` init 컨테이너가 무한 대기하며 pod가 Running 상태로 전환되지 않음

### 원인 조사
```bash
kubectl describe pod -n airflow airflow-webserver-768cb4895b-5tzqh
# → spec.initContainers{wait-for-airflow-migrations}: Back-off restarting failed container

kubectl logs -n airflow airflow-scheduler-6d4dbf4fdd-ftm65 -c wait-for-airflow-migrations
# → INFO - Waiting for migrations... N second(s) 무한 반복

kubectl get jobs -n airflow
# → No resources found
```

### 원인
- `kubectl scale` 로 pod를 내렸다 올리는 방식은 Helm hook으로 동작하는 migration job(`airflow-run-airflow-migrations`)을 재실행하지 않음
- dump 복원 후 DB의 alembic 버전이 현재 airflow 버전과 불일치하여 `airflow db check-migrations` 가 실패

### 해결
- 임시 pod를 띄워 `airflow db upgrade` 직접 실행
```bash
kubectl run airflow-db-upgrade --rm -it \
  --image=apache/airflow:2.4.1 \
  --restart=Never \
  -n airflow \
  --env="AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@10.42.0.1:5432/airflow_legacy" \
  -- airflow db upgrade
```

---

## 5. DAG 파싱 실패 및 dag_run 이력 미표시 (pickle protocol 오류)

### 문제
- dump 복원 후 일부 DAG만 표시되고 dag_run 이력이 UI에서 보이지 않음

### 원인 조사
```bash
kubectl logs -n airflow airflow-scheduler-6d4dbf4fdd-ftm65 -c scheduler 2>&1 | grep -E "error|Error"
# → ValueError: unsupported pickle protocol: 5

sudo docker exec airflow-host-postgres psql -U airflow -d airflow_legacy -c "SELECT COUNT(*) FROM dag_run;"
# → 107738 (DB에는 데이터 존재 확인)
```

### 원인
- dump 원본 서버: Python 3.8 이상 환경 (pickle protocol 5 사용)
- 현재 k3s airflow 이미지 `apache/airflow:2.4.1`: 기본 Python 3.7 (pickle protocol 최대 4)
- `rendered_task_instance_fields` 등 pickle로 직렬화된 컬럼을 역직렬화하지 못해 DAG 파싱 전체가 실패

### 해결
- `values-production.yaml`에 Python 3.8 이미지 명시
- 의아한 점: 원래 명시해놨는데 왜 안 됐는진 모르겠음. 아마도 수정하면서 지웠을 것 같다.
```yaml
images:
  airflow:
    repository: apache/airflow
    tag: "2.4.1-python3.8"
    pullPolicy: IfNotPresent
```
- helm upgrade 적용
```bash
helm upgrade airflow apache-airflow/airflow \
  -n airflow \
  -f k3s-infra/apps/airflow/values-production.yaml \
  --reuse-values \
  --version 1.7.0
```


---
k3s 환경에서 Airflow를 이관하며 겪으신 DB Dump 및 복원 트러블슈팅 과정을 나중에 다시 보거나 팀 공유용으로 활용하기 좋게 작업 순서(Workflow)에 맞추어 깔끔하게 정리했음.

---

# [Troubleshooting] k3s Airflow 이관에 따른 Postgres DB 백업 및 복원 정리

## 1. [백업] 운영 서버 DB Dump 추출 및 로컬 다운로드

보안상 외부 방화벽 포트(5432)를 열지 않고, 운영 서버 내부에서 도커 명령어로 안전하고 빠르게 덤프를 추출한 뒤 우회하여 로컬 및 온프레미스로 가져오는 방식을 채택했음.

### 1-1. Rocky 9 방화벽 규칙 원상복구 (Rollback)

임시로 열었던 방화벽 규칙이 있다면 삭제하고 닫아줌.

```bash
# 방법 A: 포트 허용을 했던 경우
sudo firewall-cmd --permanent --remove-port=5432/tcp
sudo firewall-cmd --reload

# 방법 B: 특정 IP rich-rule을 적용했던 경우
sudo firewall-cmd --permanent --remove-rich-rule='rule family="ipv4" source address="<내_로컬PC_IP>" service name="ssh" accept'
sudo firewall-cmd --reload

# 방화벽 차단 확인 (5432 관련 항목 제거 확인)
sudo firewall-cmd --list-all

```
![[TS_K3s-dump-연동-1781850278882.webp|607]]

### 1-2. 운영 서버 내 컨테이너 덤프 생성

> 주의: 파일 깨짐 방지를 위해 `docker exec` 실행 시 `-it` 대신 `-t` 옵션만 사용함.

```bash
# 1. 포스트그레스 컨테이너 이름/ID 확인
docker ps

# 2. 컨테이너 내부 pg_dump 기능을 빌려 호스트 /tmp에 덤프 파일 생성
docker exec -t <컨테이너_ID> pg_dump -U postgres -d <디비명> -F c -f /tmp/backup.dump

# 3. 덤프 파일 정상 생성 및 용량 확인
ls -lh /tmp/backup.dump
```

### 1-3. 우회 경로를 통한 덤프 파일 이관 (GCE -> 로컬 -> 온프레미스)

네트워크망 분리로 인해 단번에 전송이 불가능하여 GCE 서버 ➔ 로컬 PC ➔ 타겟 온프레미스 서버 순으로 순차 전송(SCP)했음.

```bash
# 1. GCE 서버에서 로컬 PC Downloads 폴더로 가져오기 (IAP 터널링 활용)
gcloud compute scp sychoi@de-airflow-master:/tmp/20260619_bak_for_k3s.dump \
  --tunnel-through-iap \
  --project=crowdworks-platform \
  --zone=asia-northeast1-a \
  ./Downloads/

# 2. 로컬 PC에서 최종 목적지인 온프레미스 서버(/tmp)로 전송
scp ./Downloads/20260619_bak_for_k3s.dump 192.168.10.100:/tmp/

# 3. [보안 관리] 원본 운영 서버에 남은 임시 덤프 파일 삭제
# (운영 서버 터미널에서 실행)
rm -f /tmp/backup.dump
```

---

## 2. [복원 준비] 타겟 Postgres 컨테이너 환경 점검 및 파일 연동

### 2-1. 타겟 DB 접속 실패 현상 조치

* 현상: `POSTGRES_DB=airflow_compat` 환경변수로 컨테이너가 기동되었으나, 실제 해당 DB가 존재하지 않아 `psql` 접속 실패. 기존에 데이터 디렉토리가 남아있어 초기화 스크립트가 생략된 것이 원인이었음.
* 해결: `docker inspect`를 통해 실제 내부에 존재하는 DB(`postgres`, `airflow_legacy`)를 확인한 후, 접속 시 명시적인 `-d` 옵션을 주어 접속에 성공했음.

```bash
# 환경변수 및 실제 DB 상태 점검
sudo docker inspect airflow-host-postgres --format '{{json .Config.Env}}'

# 존재하는 기본 DB 명시하여 정상 접속 성공 (PW: airflow)
sudo docker exec -it airflow-host-postgres psql -U airflow -d postgres
```
![[TS_K3s-dump-연동-1781850346379.webp]]

```bash
# 1. 컨테이너 중지 및 삭제 (볼륨은 유지됨)
sudo docker stop airflow-host-postgres
sudo docker rm airflow-host-postgres

# 2. 올바른 설정으로 재생성
sudo docker run -d \
--name airflow-host-postgres \
--restart unless-stopped \
-e POSTGRES_USER=airflow \
-e POSTGRES_PASSWORD=airflow \
-e POSTGRES_DB=airflow_legacy \
-v 38c155dc1da7f13f3601bdf27fb52fbcd05951bb2730d779e075038b2cd31275:/var/lib
/postgresql/data \
-p 5432:5432 \
postgres:13
```
- `values-production.yaml`수정했는데에도 여전히 'airflow_compat'으로 남아있어서 지우고 새로 등록해줬다.

### 2-2. 덤프 파일을 Postgres 컨테이너 내부로 복사

```bash
# 온프레미스 서버의 /tmp 파일 ➔ 도커 컨테이너 내부 /tmp로 복사
sudo docker cp /tmp/20260619_bak_for_k3s.dump airflow-host-postgres:/tmp/
```

---

## 3. [복원 진행] 트러블슈팅 Case Study

### Case 1. DROP DATABASE 실패 (세션 충돌)

* 문제: `DROP DATABASE airflow_legacy;` 수행 시 다른 세션들이 접속 중이라는 에러 발생 (`ERROR: database ... is being accessed by other users`).
* 원인: k3s 내의 Airflow Pod들이 계속해서 재연결을 시도하여, `pg_terminate_backend`로 세션을 끊어도 새로운 세션이 즉시 생성됨.
* 해결: k3s 내부 Airflow 관련 네임스페이스의 모든 Pod을 스케일 다운(`replicas=0`)한 뒤 세션을 강제 종료하고 데이터베이스를 재생성했음.

```bash
# 1. k3s Airflow 관련 Pod 전체 스케일 다운
kubectl scale deployment --all -n airflow --replicas=0
kubectl scale deployment --all -n airflow-compat-test --replicas=0

# 2. 타겟 Postgres 컨테이너에서 기존 세션 강제 종료
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'airflow_legacy' AND pid <> pg_backend_pid();"

# 3. 기존 DB 삭제 및 재생성
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "DROP DATABASE airflow_legacy;"
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "CREATE DATABASE airflow_legacy OWNER airflow;"

```

### Case 2. DROP DATABASE 트랜잭션 블록 오류

* 문제: `ERROR: DROP DATABASE cannot run inside a transaction block` 발생.
* 원인: `psql -c` 옵션 실행 시 여러 명령어를 세미콜론(`;`)으로 묶어 던지면 psql이 이를 하나의 트랜잭션 블록으로 처리함. `DROP DATABASE` 구문은 트랜잭션 내부 실행이 불가능함.
* 해결: 아래와 같이 명령어를 1줄씩 분리하여 각각 단독 실행으로 처리했음.

```bash
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "DROP DATABASE airflow_legacy;"
sudo docker exec airflow-host-postgres psql -U airflow -d postgres -c "CREATE DATABASE airflow_legacy OWNER airflow;"

```

### Case 3. 복원 후 Airflow Pod의 Init 컨테이너 무한 대기

* 문제: DB 복원 후 Pod을 다시 기동했으나, `wait-for-airflow-migrations` 단계에서 Pod이 넘어가지 못하고 무한 대기함.
* 원인: Helm의 `kubectl scale` 조절 방식은 마이그레이션 잡(`airflow-run-airflow-migrations`)을 재실행시키지 않음. 덤프한 옛날 DB의 alembic 버전과 현재 k3s Airflow 버전이 불일치하여 발생한 병목임.
* 해결: 마이그레이션을 수동으로 밀어주기 위해 임시 파드를 띄워 `airflow db upgrade` 명령을 수동 실행했음.

```bash
kubectl run airflow-db-upgrade --rm -it \
  --image=apache/airflow:2.4.1 \
  --restart=Never \
  -n airflow \
  --env="AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@10.42.0.1:5432/airflow_legacy" \
  -- airflow db upgrade

```

### Case 4. UI 상에서 DAG 파싱 실패 및 dag_run 이력 누락

* 문제: DB에는 `dag_run` 데이터가 온전히 존재함에도 Airflow Webserver UI에서 이력이 보이지 않고 일부 DAG 파싱 오류 발생.
* 원인: 스케줄러 로그 확인 결과 `ValueError: unsupported pickle protocol: 5`가 감지되었음. 원본 서버는 Python 3.8+ 환경(Pickle Protocol 5)이었던 반면, 타겟 서버의 기본 `apache/airflow:2.4.1` 이미지는 Python 3.7(Pickle Protocol 최대 4) 기반이어서 메타데이터의 직렬화 데이터를 읽지못한 것임.
* 해결: `values-production.yaml`에서 명시적으로 Python 3.8 태그 버전을 지정한 뒤 Helm 업그레이드를 수행하여 해결했음.

```yaml
# values-production.yaml 내 이미지 태그 수정
images:
  airflow:
    repository: apache/airflow
    tag: "2.4.1-python3.8"  # 기존 2.4.1에서 python3.8 지정 버전으로 변경
    pullPolicy: IfNotPresent

```

```bash
# 헬름 차트 반영
helm upgrade airflow apache-airflow/airflow \
  -n airflow \
  -f k3s-infra/apps/airflow/values-production.yaml \
  --reuse-values \
  --version 1.7.0

```