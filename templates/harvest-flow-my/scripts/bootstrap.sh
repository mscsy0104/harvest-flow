#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Update APP_VAULT_STEM before running."
fi

uv sync --all-extras
echo "Bootstrap complete. Run:"
echo "  bash scripts/run_engine.sh"
echo "  bash scripts/run_dashboard.sh"

