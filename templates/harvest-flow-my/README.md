# harvest-flow-my

Private personal instance of HarvestFlow.

## What this repo contains

- Personal `.env` values and runtime config
- Personal vault/content/theme/deploy assets
- Thin runner scripts for engine/dashboard

## Dependency strategy

This repository depends on:

- `harvest-flow` (open-source app package), or
- `harvest-flow-core` + your own app wiring

## Quick Start

```bash
cp .env.example .env
uv sync --all-extras
bash scripts/run_engine.sh
```

In another terminal:

```bash
bash scripts/run_dashboard.sh
```

