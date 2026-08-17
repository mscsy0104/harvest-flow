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

