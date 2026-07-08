---
date created: Wednesday, June 24th 2026, 2:19:57 pm
date modified: Sunday, July 5th 2026, 10:19:01 am
status: 출간
---

### 🤖 AI 자동 요약 및 인덱싱
요약:
- 공용 OS 계정으로 Bitbucket에 접근할 때 SSH 키 부재로 인해 직접적인 `git clone`이 어려운 상황이다.
- 이를 우회하기 위해 개인 팀 계정을 거쳐 레포지토리를 클론한 후, `sudo cp -r` 명령어를 사용하여 최종 목표 디렉토리로 파일을 이동시키는 방식을 사용한다.

태그:
#GitWorkflow #Bitbucket #접근제어

---

### 본문
# 배경

- Bitbucket 권한: View, Commit/PR/…, Clone,…
	- 안 되는 것: Repository Settings
- 따라서 Personal SSH Key 값을 세팅해서 공용 레포에 대한 접근을 해야한다.
- 문제: on-premise에서 OS 공용 계정(`de`)으로 관리할 때 공용 계정용 SSH Key 가 없어 git clone이 어렵다.

# 해결(우회법)

- 지금 생각해보면, `cw-de-middleware`인가 몇 가지 우리 팀 계정이 있는데 그걸로 bitbucket 로그인해서 진행할 수도 있을 것 같다.
- 우회법: 
	- Bitbucket 내 계정 -(`git clone`)→ Server 내 계정
	- `git clone`한 결과 파일을 옮기고자 하는 계정 경로로 이동시킨다.
```bash
# [내 계정]$ git clone <bitbucket repo>

# sudo cp -r <내 계정 홈 디렉토리에 clone된 repo 경로> <옮기고자 하는 대상 디렉토리 경로>
sudo cp -r /home/mscsy0104/de-data-sync-checker /homecw/de/
```