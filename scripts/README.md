# Quartz Local Preview Scripts

이 문서는 `scripts/` 아래 Quartz 관련 셸 스크립트의 용도와 사용법을 정리합니다.

## 목적

- 로컬에서 Quartz 디자인을 빠르게 확인
- 디자인 파일(`custom.scss`)을 백업/복구
- CI 배포 이전에 로컬에서 안전하게 반복 테스트

## 스크립트 구분

### 1) 로컬 미리보기 실행용

- `quartz-sync.sh`
  - Quartz 런타임 준비/업데이트
  - `quartz_content/` 동기화
  - `quartz_theme/styles/` 스타일 오버라이드 반영
  - `quartz_theme/quartz.config.yaml`이 있으면 로컬 런타임에 반영
  - `npm ci` 후 plugin restore/resolve 실행

- `quartz-preview.sh`
  - `quartz-sync.sh` 실행 후
  - `npx quartz build --serve --baseDir "/harvest-flow"`로 로컬 미리보기 서버 실행

### 2) 디자인 백업/복구 보조용

- `quartz-style-backup.sh`
  - 현재 `quartz_theme/styles/custom.scss`를 타임스탬프 파일로 백업
  - 저장 위치: `quartz_theme/styles/backups/`

- `quartz-style-restore.sh`
  - `custom.scss`를 아래 소스 중 하나로 복구
  - `default`: 최소 기본 디자인
  - `starter`: 가독성 스타터 프리셋
  - `latest`: 가장 최근 백업
  - 또는 직접 파일 경로 전달 가능

## 빠른 사용법

```bash
# 1) 로컬 미리보기 실행
bash scripts/quartz-preview.sh

# 2) 현재 디자인 백업
bash scripts/quartz-style-backup.sh

# 3) 기본 디자인으로 복구
bash scripts/quartz-style-restore.sh default

# 4) 최근 백업으로 복구
bash scripts/quartz-style-restore.sh latest
```

## 주의 사항

- 이 스크립트들은 **로컬 작업용**입니다.
- CI/GitHub Actions를 직접 수정하거나 배포를 자동으로 수행하지 않습니다.
- 최종 배포 반영은 커밋/푸시 + 워크플로우 실행이 필요합니다.
