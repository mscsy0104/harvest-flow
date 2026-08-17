# Core Boundary Checklist

Use this checklist when moving code into `harvest-flow-core`.

- [ ] Module does not import runtime config (`config.*`)
- [ ] Module does not import UI frameworks (`streamlit`)
- [ ] Module does not call external services directly (Ollama/Qdrant/GitHub)
- [ ] Module has deterministic input/output and can be unit-tested
- [ ] Side effects are delegated to interfaces from `harvest_flow/core/interfaces.py`

## Current Candidate Mapping

### Core candidates

- `harvest_flow/core/frontmatter.py`
- `harvest_flow/core/hashing.py`
- `harvest_flow/core/ids.py`
- `harvest_flow/core/time_utils.py`
- `harvest_flow/core/content.py`
- `harvest_flow/core/interfaces.py`

### App/adapters

- `app.py`
- `dashboard.py`
- `harvest_flow/database.py`
- `harvest_flow/semantic_cache.py`
- `harvest_flow/adapters/*`

