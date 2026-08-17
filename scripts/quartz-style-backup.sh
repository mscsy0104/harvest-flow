#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STYLE_DIR="$ROOT_DIR/quartz_theme/styles"
CUSTOM_FILE="$STYLE_DIR/custom.scss"
BACKUP_DIR="$STYLE_DIR/backups"

if [ ! -f "$CUSTOM_FILE" ]; then
  echo "Missing custom style file: $CUSTOM_FILE"
  exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_DIR/custom.$STAMP.scss"

cp "$CUSTOM_FILE" "$TARGET"
echo "Backup created: $TARGET"
