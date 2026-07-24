---
status: 출간
date created: Tuesday, July 7th 2026, 2:28:37 pm
date modified: Wednesday, July 8th 2026, 3:26:56 pm
post_id: 20260724-wiki-uv-c8f1
---

### 🤖 AI 자동 요약 및 인덱싱
- `uv add`와 `uv pip`는 각각 프로젝트 관리 방식의 차이를 보여줍니다. 
- `uv add/sync`는 `pyproject.toml`과 `uv.lock` 파일을 사용하는 현대적인 프로젝트 단위 관리 방식이며, `uv pip`는 기존 `pip`와 호환되는 가상환경 직접 수정 방식입니다.

# 데이터 #프로젝트관리 #가상환경

---

### 본문
# [`uv add`, `uv sync`] v. s. [`uv pip`]

두 관리 방식은 `uv`를 사용하는 철학 자체가 다릅니다.

- `uv add / sync` 방식: 현대적인 프로젝트 단위 관리 방식입니다 (`pyproject.toml`, `uv.lock` 기반).
- `uv pip` 방식: 기존 `pip`와 호환되는 가상환경 직접 수정 방식입니다. [1]

두 방법의 패키지 확인 및 관리 명령어를 한눈에 볼 수 있게 정리해 드립니다.

---

## 1. 프로젝트 관리 방식 (`uv add`, `uv sync`)

프로젝트 폴더 내에 `pyproject.toml`과 `uv.lock` 파일을 두고, 선언적으로 패키지를 관리하는 uv 권장 방식입니다. [2]

- 리스트 확인:
    
    - `uv tree` (현재 프로젝트의 의존성 구조를 트리 형태로 확인)
    - _참고: 이 방식에서는 `list`라는 단독 명령어가 없어서 전체 목록은 `pyproject.toml`을 보거나 `uv tree`를 씁니다._ [3, 4]
    
- 패키지 추가: `uv add 패키지이름`
- 패키지 삭제: `uv remove 패키지이름`
- 환경 동기화: `uv sync` (`lock` 파일 기준으로 가상환경을 강제 일치시킴) [5, 6]
- 전체 업데이트: `uv sync --upgrade`
- 특정 패키지만 업데이트: `uv sync --upgrade-package 패키지이름`

---

## 2. 전통적인 가상환경 방식 (`uv pip`)

기존의 `pip` 사용법과 100% 똑같이 동작하며, 가상환경( `.venv`) 내부를 사용자가 수동으로 조작하는 방식입니다.

- 리스트 확인: `uv pip list`
- 의존성 트리 확인: `uv pip tree`
- 업데이트 대상 확인: `uv pip list --outdated`
- 패키지 설치: `uv pip install 패키지이름`
- 패키지 삭제: `uv pip uninstall 패키지이름`
- 특정 패키지 업데이트: `uv pip install --upgrade 패키지이름`
- 전체 파일로 관리 시: `uv pip compile requirements.in -o requirements.txt` 후 `uv pip sync requirements.txt` [7, 8]

---

## 💡 주의할 점 (혼용 금지)

`uv add`로 패키지를 관리하는 프로젝트에서 `uv pip install`을 실행하면 안 됩니다. `uv pip`로 임의 설치한 패키지는 `pyproject.toml`과 `uv.lock`에 기록되지 않기 때문에, 나중에 `uv sync`를 실행하는 순간 전부 강제로 삭제됩니다. [9]

현재 하시는 것처럼 `uv add / sync` 방식을 메인으로 쭉 사용하시는 것이 가장 안전합니다.


[1] [https://sigridjin.medium.com](https://sigridjin.medium.com/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EA%B0%9C%EB%B0%9C%EC%9E%90%EB%9D%BC%EB%A9%B4-uv-%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%A9%EC%8B%9C%EB%8B%A4-546d523f7178)

[2] [https://daleseo.com](https://daleseo.com/python-uv/)

[3] [https://eumgill98.tistory.com](https://eumgill98.tistory.com/120)

[4] [https://minyeamer.github.io](https://minyeamer.github.io/blog/uv-project/)

[5] [https://eumgill98.tistory.com](https://eumgill98.tistory.com/120)

[6] [https://wikidocs.net](https://wikidocs.net/305858)

[7] [https://wikidocs.net](https://wikidocs.net/blog/@jaehong/14017/)

[8] [https://incodom.kr](https://incodom.kr/uv)

[9] [https://daleseo.com](https://daleseo.com/python-uv/)



# 패키지 확인 및 관리
## 주로 `uv tree`

- 메인 패키지만 확인하고 싶을 땐: `uv tree -d 1`

## 가끔 `pyproject.toml`

- `uv add`로 패키지를 추가하면 **`pyproject.toml` 파일의 `dependencies` 항목**에 자동으로 기록됨. 그러니 문서를 확인해도 됨.

## 보조 수단 `uv pip`

- "그래도 기존 `pip list`처럼 하위 의존성을 포함한 **전체 설치 목록을 일렬로 평평하게(Flat)** 보고 싶다" 하실 때만 예외적으로 사용
---
- **기본 패키지 확인:** `uv pip list` (현재 가상환경에 설치된 패키지와 버전 표시)
- **의존성 트리 확인:** `uv pip tree` (패키지 간의 종속성을 트리 구조로 확인)
- **업데이트 필요한 패키지:** `uv pip list --outdated`
- **requirements.txt 형식 확인:** `uv pip freeze`


# 패키지 업그레이드

`uv add`와 `uv sync` 중심의 프로젝트 관리 방식을 쓰고 계셨군요! 그 방식이 `uv`가 권장하는 가장 올바르고 깔끔한 워크플로우입니다.

이 경우 예전에 쓰던 `pip` 스타일 명령어 대신, `uv.lock` 파일과 `pyproject.toml`을 갱신하는 아래의 전용 명령어를 사용하셔야 합니다. [1, 2]

---

## 1. 오래된 패키지 전체를 한 번에 최신화하기

`pyproject.toml`에 허용된 버전 범위 내에서 모든 패키지를 최신 버전으로 올리고 로컬 환경과 동기화합니다. [Astral Docs](https://docs.astral.sh/uv/concepts/projects/sync/)에 따르면, 이 과정에서 `uv.lock` 파일이 자동으로 최신 정보로 갱신됩니다. [1, 3]

```bash
uv sync --upgrade
```

_(또는 로컬 환경 동기화 없이 락파일만 먼저 업데이트하려면 `uv lock --upgrade`를 사용해도 됩니다 [Medium](https://medium.com/@utkarshshukla.author/uv-revolutionizing-python-package-management-38899ff2f40a).)_ [4]

## 2. 특정 패키지만 골라서 최신화하기

다른 패키지는 그대로 두고, 원하는 패키지 딱 하나만 최신 버전으로 업데이트하고 싶을 때 사용합니다 [위키독스](https://wikidocs.net/305831).

```bash
uv sync --upgrade-package 패키지이름
```

## 3. pyproject.toml의 버전 제한 자체를 새로 고치고 싶을 때

만약 `pyproject.toml`에 `requests>=2.30.0` 처럼 하한선이 걸려있는데, 최신 버전인 `2.32.0` 기반으로 최소 요구 버전을 아예 상향하고 싶다면 `uv add`를 다시 실행하시면 됩니다 [Astral Docs](https://docs.astral.sh/uv/concepts/projects/dependencies/). [1]

```bash
uv add 패키지이름
```

이미 설치된 패키지라도 `uv add 패키지이름`을 다시 입력하면, `uv`가 최신 버전을 찾아서 `pyproject.toml` 기록을 알아서 업데이트하고 설치까지 끝마칩니다 Astral Docs.

---

요약하자면:  
평소처럼 `uv sync`를 쓰시되 뒤에 `--upgrade` 플래그만 붙여서 실행하시면 해결됩니다!

[1] [https://github.com](https://github.com/astral-sh/uv/issues/6781)

[2] [https://sigridjin.medium.com](https://sigridjin.medium.com/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EA%B0%9C%EB%B0%9C%EC%9E%90%EB%9D%BC%EB%A9%B4-uv-%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%A9%EC%8B%9C%EB%8B%A4-546d523f7178)

[3] [https://flocode.substack.com](https://flocode.substack.com/p/044-python-environments-again-uv)

[4] [https://devocean.sk.com](https://devocean.sk.com/blog/techBoardDetail.do?ID=167420&boardType=techBlog)



# Downgrade

- 업데이트 도중 패키지 간의 버전 충돌(Dependency Conflict) 에러가 발생했거나, 특정 패키지를 이전 버전으로 다운그레이드하는 방법
---
`uv add`와 `uv sync` 기반의 프로젝트 관리 환경에서 버전 충돌(Dependency Conflict)이 발생했을 때 해결하는 방법과, 특정 패키지를 이전 버전으로 다운그레이드하는 방법을 정리해 드립니다.

`uv`는 기본적으로 아주 강력하고 엄격한 의존성 분석기(Resolver)를 가지고 있어, 충돌이 나면 어떤 패키지들끼리 얽혀서 문제가 되었는지 터미널에 아주 상세하게 알려줍니다.

---

## 1. 특정 패키지 이전 버전으로 다운그레이드하기

가장 간단한 방법입니다. `uv add` 명령어 뒤에 원하는 특정 버전을 명시해주면 `uv`가 `pyproject.toml`과 `uv.lock`을 해당 버전에 맞게 강제로 새로 고칩니다.

- 특정 버전으로 지정 (예: 2.30.0 버전으로 다운그레이드)
    
    ```bash
    uv add "requests==2.30.0"
    ```
    
- 상한선 지정 (예: 3.0.0 미만 버전 중 가장 최신 버전으로 다운그레이드)
    
    ```bash
    uv add "requests<3.0.0"
    ```
    
    - _주의: 터미널에서 `==`, `<`, `>` 같은 기호를 쓸 때는 인식 오류를 막기 위해 패키지 이름을 웅클린 따옴표(`""`)로 감싸주는 것이 좋습니다._
    

---

## 2. 패키지 업데이트 중 버전 충돌(Dependency Conflict) 해결하기

예를 들어, 내가 `A`라는 패키지를 업데이트하려고 `uv sync --upgrade-package A`를 쳤는데 "A는 내부적으로 B>=2.0을 요구하는데, 현재 프로젝트의 C가 B<=1.5를 요구하고 있어서 충돌이 난다"는 에러가 발생한 상황입니다.

이때는 크게 3가지 방법으로 해결합니다.

## 방법 A: 충돌을 일으키는 다른 패키지도 같이 업데이트하기 (가장 추천)

`A`를 업데이트하기 위해 `B`도 같이 올라가야 하는데, `C`가 발목을 잡고 있다면 `C`도 함께 업데이트 대상에 포함시켜 버리는 것입니다.

```bash
uv sync --upgrade-package A --upgrade-package C
```

이렇게 하면 `uv`가 두 패키지의 요구사항을 동시에 만족하는 교집합 버전을 다시 계산해서 최신화해 줍니다.

## 방법 B: 일시적으로 특정 패키지의 버전 고정하기 (`--override`)

협업 중이거나 시스템 구조상 발목을 잡는 패키지(`C`)의 버전을 당장 `pyproject.toml`에서 바꾸기 곤란할 때가 있습니다. 이럴 때는 임시로 특정 버전을 강제 적용하여 충돌을 우회할 수 있습니다.

1. 프로젝트 루트에 `overrides.txt`라는 파일을 하나 만듭니다.
2. 파일 안에 충돌을 해결할 강제 버전을 적습니다 (예: `B==2.1.0`).
3. 아래 명령어로 동기화합니다.

```bash
uv sync --override overrides.txt
```

## 방법 C: pyproject.toml에서 허용 범위(Constraints) 넓혀주기

만약 `pyproject.toml` 파일에 내가 직접 `C==1.5.0`처럼 버전을 너무 꽉 막히게 고정해 두어서 충돌이 난 것이라면, 파일을 열어 `C>=1.5.0` 또는 `C^1.5` 형태로 범위를 넓혀준 뒤 다시 `uv sync`를 실행하면 자연스럽게 해결됩니다.

---

요약하자면:  
버전을 내릴 때는 `uv add "패키지==버전"`을 쓰면 되고, 충돌이 날 때는 에러 메시지에서 원인이 된 패키지를 찾아서 `--upgrade-package` 옵션에 충돌 패키지들을 콤마 없이 나란히 같이 적어주면 됩니다!



# Workspace

 프로젝트 루트 경로에 `pyproject.toml`이 있는데 
 데이터 프로세싱할 때는 프로젝트별로 사용하는 패키지가 비슷한데 
 매번 `uv init` 하기에 용량 차지가 클 것 같아 따로 구분해서 진행하려고 하다 'workspace' 개념을 이용함.
 
 루트 경로에 `pyproject.toml`에 패키지 목록이 있고, 
 루트 하위 개별 프로젝트 경로에도 `pyproject.toml` 이 있는데, 
 처음에는 괜찮은 생각 같았지만
 오히려 uv 관련해서 고민할 게 많아져서
 루트 경로에 두고 명령어를 다음과 같이 타고 들어가서 실행하기로 함.

```
uv run proj-12345/src/main.py
```


# Prd v. s. Dev

- 작업 중인 프로젝트에 배포용 운영 환경(Production) 과 개발자용 테스트 환경(Development) 의 패키지를 분리해서 관리하는 방법(`uv add --dev`)
---
`uv add --dev`를 사용하면 배포(운영) 환경용 패키지와 로컬 개발/테스트용 패키지를 명확히 분리하여 관리할 수 있습니다. [1, 2, 3]

`uv`는 개발(dev) 환경 패키지를 `pyproject.toml` 내부의 `[dependency-groups]` 영역에 따로 기록하여 운영 환경과 격리합니다. 환경별 명령어 사용법을 정리해 드립니다. [1, 3, 4]

---

## 1. 패키지 추가할 때 분리하기

- 배포(운영)용 패키지 추가: 일반적인 방식으로 추가합니다.
    
    ```bash
    uv add fastapi gunicorn
    ```
    
    - _결과:_ `pyproject.toml`의 `[project.dependencies]`에 등록되어 실제 서비스 실행에 포함됩니다. [4, 5, 6, 7]
    
- 개발/테스트용 패키지 추가: `--dev` 플래그를 붙여서 추가합니다.
    
    ```bash
    uv add --dev pytest ruff black
    ```
    
    - _결과:_ `pyproject.toml`의 `[dependency-groups] dev` 구역에 등록되며 배포 시 제외할 수 있습니다. [5, 6]
    

---

## 2. 환경별 패키지 동기화(설치) 및 배포하기

실제 서버(운영 환경)와 내 컴퓨터(개발 환경)에서 `uv sync` 옵션을 다르게 주어 필요한 것만 설치합니다.

- 로컬 개발 환경 (전체 설치):
    
    ```bash
    uv sync
    ```
    
    - _동작:_ 기본적으로 `uv sync`만 치면 운영용 패키지와 개발용(`--dev`) 패키지가 모두 설치됩니다. [1, 4, 8]
    
- 운영/배포 환경 (개발용 제외):
    
    ```bash
    uv sync --no-dev
    ```
    
    - _동작:_ `pytest`나 `ruff` 같은 개발용 패키지를 쏙 빼고 실제 서비스 구동에 필요한 배포용 패키지만 깔끔하게 가상환경에 설치합니다. Docker 이미지를 빌드하거나 CD(지속적 배포) 파이프라인을 구축할 때 이 명령어를 사용하시면 됩니다. [6, 8, 9, 10]
    

---

## 3. 분리된 리스트 확인하기

앞서 배운 `uv tree` 명령어를 활용하면 어떤 패키지가 어디에 속해있는지 쉽게 파악할 수 있습니다.

- 전체 구조 트리 확인: `uv tree` (어떤 개발 패키지가 설치되었는지 트리 하단에서 확인 가능)
- 운영 환경 패키지만 필터링해서 확인:
    
    ```bash
    uv tree --no-dev
    ```
    
    [5, 8]


[1] [https://pydevtools.com](https://pydevtools.com/handbook/explanation/understanding-dependency-groups-in-uv/)

[2] [https://docs.mila.quebec](https://docs.mila.quebec/userguides/python_uv/)

[3] [https://docs.astral.sh](https://docs.astral.sh/uv/concepts/projects/dependencies/)

[4] [https://github.com](https://github.com/astral-sh/uv/issues/10813)

[5] [https://medium.com](https://medium.com/@gnetkov/start-using-uv-python-package-manager-for-better-dependency-management-183e7e428760)

[6] [https://lcmartinez.com](https://lcmartinez.com/python-dependencies)

[7] [https://toyourlight.tistory.com](https://toyourlight.tistory.com/155)

[8] [https://pydevtools.com](https://pydevtools.com/handbook/explanation/understanding-dependency-groups-in-uv/)

[9] [https://github.com](https://github.com/astral-sh/uv/issues/16257)

[10] [https://dev.to](https://dev.to/thomas_bury_b1a50c1156cbf/mastering-python-project-management-with-uv-part-3-mlops-38e2)



질문하신 두 가지 내용 모두 핵심을 정확하게 짚으셨습니다! 이해하신 내용이 맞는지 상세한 설명과 함께 점검해 드릴게요.

---

## 1. 첫 번째 질문 점검: 배포할 때 `uv sync --no-dev`가 맞는가?

네, 완벽하게 정확합니다!

로컬 컴퓨터에서는 테스트와 코드 관리가 필요하므로 `uv sync`로 전체 패키지를 설치해 개발합니다. 이후 실제 서버(AWS, Docker 등)로 코드를 옮긴 뒤 터미널에서 `uv sync --no-dev`를 실행하면, 개발용 패키지는 제외하고 운영에 꼭 필요한 패키지만 가상환경에 아주 깔끔하게 설치됩니다.

---

## 2. 두 번째 질문 점검: 운영(Prod)과 개발(Dev) 패키지 구분 기준

"프로젝트 만들 때는 일단 다 필요하니까 설치하는 것 아닌가?"라는 의문은 매우 자연스럽습니다. 구분하는 가장 쉬운 기준은 "이 패키지가 없으면 실제 사용자가 서비스를 이용할 때 에러가 나는가?"를 생각해보는 것입니다.

## 💡 운영 환경(Production) 패키지 기준

- 정의: 실제 서버에서 프로그램이 '실행'되고 '동작'하는 데 반드시 필요한 패키지입니다.
- 예시:
    
    - 웹 서버 프레임워크 (`fastapi`, `django`, `flask`)
    - 데이터베이스 연결 라이브러리 (`sqlalchemy`, `psycopg2`)
    - 데이터 처리 및 계산 도구 (`pandas`, `numpy`, `requests`)
    
- 판단 질문: "서버에서 이 패키지 없으면 웹사이트 안 뜨거나 기능이 먹통 되나?" ➡️ Yes면 무조건 일반 설치 (`uv add`)

## 🛠️ 개발 환경(Development) 패키지 기준

- 정의: 코드를 작성하고, 검사하고, 테스트하는 '개발자 지갑/수단'일 뿐, 실제 서비스 운영 자체에는 아무런 영향을 주지 않는 패키지입니다.
- 예시:
    
    - 코드 테스트 도구 (`pytest`, `unittest`)
    - 코드 스타일 및 오류 검사기 (`ruff`, `black`, `flake8`)
    - 개발 편의 도구 (`ipython`, `jupyter`)
    
- 판단 질문: "이거 없어도 서버 실행되고 사용자가 기능 쓰는 데 문제없나?" ➡️ Yes면 개발용 설치 (`uv add --dev`)

---

## 짚고 넘어가기: 배포 환경에서 개발 패키지를 빼야 하는 이유

전부 다 배포해도 프로그램은 작동합니다. 하지만 굳이 빼는 이유는 3가지 때문입니다.

1. 보안: 개발용 도구에 포함된 취약점이 해킹의 통로가 될 수 있습니다.
2. 용량 축소: Docker 이미지 용량이 줄어들어 서버 배포 속도가 빨라집니다.
3. 충돌 방지: 불필요한 패키지가 섞여서 발생할 수 있는 잠재적 버전 오류를 막습니다.