# Repository Split Guide

This project is being split into three repositories:

- `harvest-flow-core`: pure business/domain logic
- `harvest-flow`: open-source reference app and adapters
- `harvest-flow-my`: personal blog/content/deploy setup

## Boundary Rules

### Keep in core

- Markdown/frontmatter processing
- Workflow validation rules
- Time/hash/id helper functions
- Abstract interfaces (`VectorDB`, `MetadataDB`, `SSGPublisher`)

### Keep in open-source app

- Runtime engine (`app.py`)
- Dashboard (`dashboard.py`)
- Adapter implementations under `harvest_flow/adapters/`
- Config loading and environment wiring
- Sample-first runtime paths (`samples/notes_vault`, `samples/publish_content`)

### Keep in personal repo

- `quartz_content/`
- personal Quartz theme files and backups
- personal deploy workflow and secrets

## Migration Steps

1. Stabilize package/install flow (`pyproject.toml`, editable install).
2. Keep defaults generic in `.env.example`.
3. Publish `harvest-flow` OSS repo with sample content only.
4. Move personal content and deploy automation to `harvest-flow-my`.

## Public API Contract (Core)

- `harvest-flow` and `harvest-flow-my` must import from `harvest_flow_core` public modules only:
  - `content`, `frontmatter`, `hashing`, `ids`, `interfaces`, `time_utils`
- Do not import private internals or use `src.*` paths.
- Any change to `harvest_flow_core.__all__` requires API change disclosure in PR.

## Release Promotion and Rollback

- Promotion order is fixed: `harvest-flow-core` -> `harvest-flow` -> `harvest-flow-my`.
- Rollback order is reverse-only when required: `harvest-flow-my` -> `harvest-flow` -> `harvest-flow-core`.
- Core release candidates must publish compatibility notes before app update begins.
- Detailed gate ownership and rollback routine: `docs/RELEASE_PROMOTION_PLAYBOOK.md`.

## PR Checklist (Required)

- [ ] I verified the change belongs to the correct repo boundary (core/app/my).
- [ ] I disclosed public API impact (`breaking` or `non-breaking`) when touching core symbols.
- [ ] I ran required smoke checks (core unit, app compatibility/integration, my personal smoke).

