#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${QUARTZ_RUNTIME_DIR:-$ROOT_DIR/__quartz_runtime}"
CONTENT_SRC="${CONTENT_SRC:-$ROOT_DIR/quartz_content}"
THEME_SRC="${THEME_SRC:-$ROOT_DIR/quartz_theme}"
QUARTZ_REPO="${QUARTZ_REPO:-https://github.com/jackyzha0/quartz.git}"
QUARTZ_REF="${QUARTZ_REF:-}"
PROJECT_BASE_DIR="${PROJECT_BASE_DIR:-/harvest-flow}"
PROJECT_BASE_URL="${PROJECT_BASE_URL:-localhost:8080${PROJECT_BASE_DIR}}"
RESTORE_PLUGINS="${QUARTZ_RESTORE_PLUGINS:-1}"

if [ ! -d "$CONTENT_SRC" ]; then
  echo "Missing content directory: $CONTENT_SRC"
  exit 1
fi

if [ ! -d "$RUNTIME_DIR/.git" ]; then
  echo "Cloning Quartz runtime into $RUNTIME_DIR"
  if [ -n "$QUARTZ_REF" ]; then
    git clone --depth 1 --branch "$QUARTZ_REF" "$QUARTZ_REPO" "$RUNTIME_DIR"
  else
    git clone --depth 1 "$QUARTZ_REPO" "$RUNTIME_DIR"
  fi
else
  echo "Updating existing Quartz runtime in $RUNTIME_DIR"
  git -C "$RUNTIME_DIR" fetch --depth 1 origin
  if [ -n "$QUARTZ_REF" ]; then
    git -C "$RUNTIME_DIR" fetch --depth 1 origin "$QUARTZ_REF" || true
    git -C "$RUNTIME_DIR" checkout --force "$QUARTZ_REF"
  else
    default_branch="$(git -C "$RUNTIME_DIR" remote show origin | awk '/HEAD branch/ {print $NF}')"
    git -C "$RUNTIME_DIR" checkout --force "$default_branch"
    git -C "$RUNTIME_DIR" reset --hard "origin/$default_branch"
  fi
fi

echo "Syncing content from $CONTENT_SRC"
rm -rf "$RUNTIME_DIR/content"
mkdir -p "$RUNTIME_DIR/content"
cp -R "$CONTENT_SRC"/. "$RUNTIME_DIR/content/"

if [ ! -f "$RUNTIME_DIR/content/index.md" ]; then
  printf '%s\n' \
    '---' \
    'title: HarvestFlow' \
    '---' \
    '' \
    '# HarvestFlow Knowledge Garden' \
    '' \
    '자동 출하된 지식 노트 모음입니다.' \
    > "$RUNTIME_DIR/content/index.md"
fi

if [ -d "$THEME_SRC/styles" ]; then
  echo "Applying local style overrides from $THEME_SRC/styles"
  mkdir -p "$RUNTIME_DIR/quartz/styles"
  cp -R "$THEME_SRC/styles"/. "$RUNTIME_DIR/quartz/styles/"
fi

if [ -f "$THEME_SRC/quartz.config.yaml" ]; then
  echo "Applying local config override from $THEME_SRC/quartz.config.yaml"
  cp "$THEME_SRC/quartz.config.yaml" "$RUNTIME_DIR/quartz.config.yaml"
fi

if [ ! -f "$RUNTIME_DIR/quartz.config.yaml" ] && [ -f "$RUNTIME_DIR/quartz.config.default.yaml" ]; then
  cp "$RUNTIME_DIR/quartz.config.default.yaml" "$RUNTIME_DIR/quartz.config.yaml"
fi

if [ -f "$RUNTIME_DIR/quartz.config.yaml" ]; then
  python3 - "$RUNTIME_DIR/quartz.config.yaml" "$PROJECT_BASE_URL" <<'PY'
import re
import sys

config_path, base_url = sys.argv[1], sys.argv[2]
with open(config_path, "r", encoding="utf-8") as f:
    text = f.read()

updated = re.sub(r"^([ \t]*baseUrl:[ \t]*).*$", rf"\1{base_url}", text, count=1, flags=re.M)
if updated != text:
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(updated)
PY
fi

cd "$RUNTIME_DIR"

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

if [ "$RESTORE_PLUGINS" = "1" ]; then
  npx quartz plugin restore
  npx quartz plugin resolve
fi

echo
echo "Quartz runtime is ready:"
echo "  RUNTIME_DIR=$RUNTIME_DIR"
echo "  PROJECT_BASE_DIR=$PROJECT_BASE_DIR"
echo "  PROJECT_BASE_URL=$PROJECT_BASE_URL"
