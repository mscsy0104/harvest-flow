#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/commit_content.sh \"content: your message\" [--push]"
  exit 1
fi

MESSAGE="$1"
PUSH_AFTER="${2:-}"

# 블로그 콘텐츠만 스테이징
git add -- "quartz_content/"

if [ -z "$(git diff --cached --name-only)" ]; then
  echo "No staged content changes under quartz_content/."
  exit 1
fi

git commit -m "$MESSAGE"
echo "Committed content-only changes."

if [ "$PUSH_AFTER" = "--push" ]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  git push origin "$BRANCH"
  echo "Pushed to origin/$BRANCH."
fi
