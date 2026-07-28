---
status: 출간
date created: Tuesday, March 3rd 2026, 4:08:40 pm
date modified: Tuesday, July 28th 2026, 11:33:05 pm
post_id: 20260728-ts-20260303-airflow-hostname-0652
---

### 🤖 AI 자동 요약 및 인덱싱
- Celery worker 인식 시간을 30분 이내로 단축하기 위해, Hostname 명시화를 통해 Worker 식별자 고정 및 배포 즉시 가용 상태 유지.  Airflow 환경 변수 수정 후 Docker Update 시 발생하는 지연 문제 해결.
#데이터 #배포 #생산성

---

### 본문
celery hostname



# 배경

- 현상: Airflow 환경변수 수정 후 Docker Update 시, Celery Worker 인식하기까지 약 30분 이상의 지연 시간 발생.

- 원인 추정: Hostname이 암시적으로 설정돼 컨테이너 ID를 사용하게 되는데, 배포 시마다 워커의 식별자가 변경됨. 이로 인해 기존 Worker의 타임아웃을 기다리는 대기 시간이 발생하고 추적성이 저하됨.

- 목표: Hostname 명시화를 통해 Worker 식별자를 고정하고 배포 즉시 Worker가 가용 상태가 되도록 최적화.

# 해결 방법

- docker-compose.yaml 설정에서 호스트네임을 강제하고, Airflow 컨텍스트에서 명령어가 실행되도록 수정함.

## docker-compose.yaml
```
airflow-worker:
  <<: *airflow-common
  # 1. 컨테이너 OS 레벨의 호스트네임 고정
  hostname: google-airflow-worker
  # 2. Airflow 진입점(Entrypoint)을 통한 명령어 실행
  command: airflow celery worker
  healthcheck:
    test:
      - "CMD-SHELL"
      - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
    interval: 10s
    timeout: 10s
    retries: 5
```

# 결과 및 분석

- **결과:** 배포 후 약 30초 이내에 워커가 정상 등록됨(기존 대비 약 60배 속도 향상).
    
- **분석:**
    
    - **명령어 차이 (**celery worker **vs** airflow celery worker**):** 단순히 celery worker만 실행할 경우 Airflow의 설정 파일(airflow.cfg)이나 환경변수 로딩 과정이 누락되는 것 같음. airflow를 앞에 붙여 실행해야 Airflow 환경 내에서 정의된 HOSTNAME 변수와 설정값을 Celery가 올바르게 참조하도록 함.
        
    - **배포 지연 해소:** 호스트네임을 고정함으로써, 새로운 컨테이너가 떠도 RabbitMQ(Broker) 입장에서는 동일한 워커가 재시작된 것으로 인식함. 따라서 기존 워커의 세션을 만료시키기 위한 불필요한 대기 시간(30분)이 사라짐.


![](99_Attachments/Log_Celery-hostname-명시화로-도커-컨테이너-추적성-높이기_1.webp)