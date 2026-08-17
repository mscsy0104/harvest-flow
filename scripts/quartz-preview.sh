#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${QUARTZ_RUNTIME_DIR:-$ROOT_DIR/__quartz_runtime}"
PROJECT_BASE_DIR="${PROJECT_BASE_DIR:-/harvest-flow}"

"$ROOT_DIR/scripts/quartz-sync.sh"

cd "$RUNTIME_DIR"

echo
echo "Starting local Quartz preview server..."
echo "Open: http://localhost:8080${PROJECT_BASE_DIR}/"
echo

npx quartz build --serve --baseDir "${PROJECT_BASE_DIR}"
