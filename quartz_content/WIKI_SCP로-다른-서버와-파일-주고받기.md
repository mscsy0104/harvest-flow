---
date created: Wednesday, June 24th 2026, 9:44:39 am
date modified: Monday, July 6th 2026, 10:18:58 am
status: 출간
post_id: 20260731-wiki-scp-1d2f
---

### 🤖 AI 자동 요약 및 인덱싱
- 본문은 GCE 서버에서 On-Premise 환경으로 파일 주고 받기 위한 SSH 터널링을 우회하는 방법들을 설명하고, SCP를 사용하여 다른 서버에 파일을 전송하는 방법을 제시합니다.
#데이터 #파일전송 #SCP

#태그1 #GCE #SSH 터널링

---

### 본문
# SCP로 다른 서버와 파일 주고 받기 

# 🖥️ 📁 ↔ 🖥️
- GCE에서 On-Premise로 파일 주고 받으려면 SSH 터널링을 가능하게 해야하는데, 인프라팀에 요청하기 전 우회하는 방법을 써보자.
    - 이유: 1번 쓰고 안 쓴다면 요청하는 복잡한 단계를 밟지 않는 게 더 효율적임. 실제로 GCE 서버 몇 개는 정리할 거라 더욱 적합함.
- 한 번에 통신이 불가능한 경우, 다음과 같이 로컬로 내려받은 뒤 보내주는 방식을 취한다.
- 사용 기술: `scp`
## 1. SCP로 다른 서버에 있는 파일 받기

- 방법 2가지
	1. `scp <해당 계정>@<파일 있는 서버명>:<파일 경로> <내려받을 로컬 디렉토리 경로>`
		: 파일을 로컬로 내려받기.
	2. `gcloud compute scp <서버명(VM명)>:<파일 경로> <내려받을 로컬 디렉토리 경로> --zone <해당 VM zone> [--tunnel-through-iap]`
		: GCE 파일을 로컬로 내려받기(tunneling 옵션은 보안상 SSH 터널링 막아놔서 설정한 상태라 한 것).
```bash
# On-Premise cw-workstation 데이터를 로컬로 내려받기
scp mscsy0104@cw-workstation:/home/mscsy0104/log_20260624.json ~/Downlodas

# GCE de-api 데이터를 로컬로 내려받기
gcloud compute scp de-api:/home/sychoi/dump.rdb ~/Downloads --zone asia-northeast1-a --tunnel-through-iap
```

## 2. SCP로 다른 서버로 파일 보내기

- 방법
	1. `scp <로컬 파일 경로> <해당 계정>@<보낼 서버명>:<보낼 디렉토리 경로>`
	2. `gcloud compute scp <로컬 파일 경로> <해당 계정>@<보낼 서버명(VM명)>:<보낼 디렉토리 경로> --zone <해당 VM zone> --tunnel-through-iap`