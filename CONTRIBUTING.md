# Contributing to HarvestFlow

## Development Setup

1. Install `uv` and Python 3.12+.
2. Clone the repository.
3. Install dependencies:
   - `uv sync --all-extras`
4. Run local checks:
   - `uv run pytest`
   - `uv run ruff check harvest_flow tests`

## Editable Install

- `uv pip install -e .`
- Optional dashboard dependencies:
  - `uv pip install -e ".[dashboard]"`

## Running Locally

- Engine: `uv run harvest-flow-engine`
- Dashboard: `uv run harvest-flow-dashboard`

## Core vs App Boundary

- Put tool-agnostic business logic in `harvest_flow/core/`.
- Put runtime integrations (DB, SSG, UI, model clients) in adapter/app layers.
- New backend integrations should implement interfaces from `harvest_flow/core/interfaces.py`.
- Prefer importing core logic from `harvest_flow_core` package public modules.
- Never import core internals with `src.*` or private module paths.

## Pull Requests

1. Keep PRs small and focused.
2. Add/update docs for user-visible behavior changes.
3. Do not commit private content (`notes_vault` real data, local `.env`, personal blog content).
4. Include an API change disclosure when changing `harvest_flow_core` public symbols.

### Required PR Checklist

- [ ] Boundary ownership confirmed (core/app/my target is correct).
- [ ] API change classification included (`breaking` or `non-breaking`) when relevant.
- [ ] Smoke checks executed for impacted repos.
- [ ] Release order impact noted (`core -> app -> my`) if this affects shared contracts.

