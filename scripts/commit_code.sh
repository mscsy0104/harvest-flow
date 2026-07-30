#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/commit_code.sh \"feat: your message\" [--push]"
  exit 1
fi

MESSAGE="$1"
PUSH_AFTER="${2:-}"

# 코드/설정 파일만 명시적으로 스테이징 (콘텐츠 폴더 제외)
git add -- \
  "app.py" \
  "dashboard.py" \
  "dashboard copy.py" \
  "src/" \
  "config/" \
  "scripts/" \
  ".github/" \
  ".gitignore" \
  "README.md" \
  "pyproject.toml" \
  "uv.lock" \
  ".python-version"

if [ -z "$(git diff --cached --name-only)" ]; then
  echo "No staged code/config changes in predefined paths."
  exit 1
fi

git commit -m "$MESSAGE"
echo "Committed code/config-only changes."

if [ "$PUSH_AFTER" = "--push" ]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  git push origin "$BRANCH"
  echo "Pushed to origin/$BRANCH."
fi
