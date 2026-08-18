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

### Pin/Update Guidance

- Pin `harvest-flow` to a tested release/tag for personal stability.
- Only upgrade after upstream promotion is complete in this order: `core -> app -> my`.
- If an upgrade fails personal smoke checks, revert `harvest-flow-my` first, then coordinate app/core rollback.

### Personal Smoke Runbook

1. `uv sync --all-extras`
2. `bash scripts/run_engine.sh` and verify startup succeeds.
3. Move one sample note through review -> publish-ready stage.
4. Run `bash scripts/run_dashboard.sh` and verify dashboard loads and query path responds.
5. Record upgraded versions and smoke result in your private release log.

### PR Checklist (when this repo has PR workflow)

- [ ] Boundary ownership is personal-ops only (no shared core/app logic changes).
- [ ] Upstream versions are pinned to approved core/app release sequence.
- [ ] Personal smoke runbook completed after version updates.

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

