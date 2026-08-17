#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Run: cp .env.example .env"
  exit 1
fi

uv run harvest-flow-dashboard

