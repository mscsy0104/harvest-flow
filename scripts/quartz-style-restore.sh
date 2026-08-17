#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STYLE_DIR="$ROOT_DIR/quartz_theme/styles"
CUSTOM_FILE="$STYLE_DIR/custom.scss"
DEFAULT_FILE="$STYLE_DIR/default.custom.scss"
STARTER_FILE="$STYLE_DIR/starter.readable.scss"
BACKUP_DIR="$STYLE_DIR/backups"
MODE="${1:-default}"

mkdir -p "$BACKUP_DIR"

restore_from_file() {
  local src="$1"
  if [ ! -f "$src" ]; then
    echo "Source style not found: $src"
    exit 1
  fi
  cp "$src" "$CUSTOM_FILE"
  echo "Restored custom.scss from: $src"
}

case "$MODE" in
  default)
    restore_from_file "$DEFAULT_FILE"
    ;;
  starter)
    restore_from_file "$STARTER_FILE"
    ;;
  latest)
    latest_file="$(ls -1t "$BACKUP_DIR"/custom.*.scss 2>/dev/null | head -n 1 || true)"
    if [ -z "${latest_file:-}" ]; then
      echo "No backup files found in $BACKUP_DIR"
      exit 1
    fi
    restore_from_file "$latest_file"
    ;;
  *)
    if [ -f "$MODE" ]; then
      restore_from_file "$MODE"
    else
      echo "Usage: bash scripts/quartz-style-restore.sh [default|starter|latest|/path/to/file.scss]"
      exit 1
    fi
    ;;
esac
