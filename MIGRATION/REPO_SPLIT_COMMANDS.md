# Repository Split Command Sequence

This guide creates three repositories from the current `harvest_flow` working tree:

- `harvest-flow-core` (pure core package)
- `harvest-flow` (open-source app/reference implementation)
- `harvest-flow-my` (private personal instance)

## 0) Prerequisites

- `uv`, `git`, `rsync`, `gh` installed
- GitHub authentication completed (`gh auth login`)
- Current repository is clean enough to copy from

Assume:

```bash
export SRC_REPO="$HOME/projects/harvest_flow"
export TARGET_ROOT="$HOME/projects/split-targets"
mkdir -p "$TARGET_ROOT"
```

## 1) Create `harvest-flow` (open-source app repo)

```bash
mkdir -p "$TARGET_ROOT/harvest-flow"
rsync -a --delete \
  --exclude ".git/" \
  --exclude ".env" \
  --exclude "obsidian_vault/" \
  --exclude "logs/" \
  --exclude "qdrant_local/" \
  --exclude "pipeline_metadata.db" \
  --exclude "quartz_content/" \
  --exclude "quartz_theme/styles/backups/" \
  "$SRC_REPO/" "$TARGET_ROOT/harvest-flow/"
```

Then initialize/push:

```bash
cd "$TARGET_ROOT/harvest-flow"
git init
git add .
git commit -m "Initialize harvest-flow open source repository"
gh repo create harvest-flow --public --source=. --remote=origin --push
```

## 2) Create `harvest-flow-core` (core-only repo)

```bash
mkdir -p "$TARGET_ROOT/harvest-flow-core"
rsync -a --delete \
  --exclude ".git/" \
  "$SRC_REPO/harvest_flow/core/" "$TARGET_ROOT/harvest-flow-core/src/harvest_flow_core/"
```

Copy minimal metadata/docs:

```bash
cp "$SRC_REPO/LICENSE" "$TARGET_ROOT/harvest-flow-core/"
cp "$SRC_REPO/docs/CORE_BOUNDARY_CHECKLIST.md" "$TARGET_ROOT/harvest-flow-core/CORE_BOUNDARY_CHECKLIST.md"
cp "$SRC_REPO/README.md" "$TARGET_ROOT/harvest-flow-core/README.md"
```

Create a core `pyproject.toml` (example):

```bash
cat > "$TARGET_ROOT/harvest-flow-core/pyproject.toml" <<'EOF'
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "harvest-flow-core"
version = "0.1.0"
description = "Core business logic for HarvestFlow."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
dependencies = ["pyyaml>=6.0.3"]

[tool.setuptools.packages.find]
where = ["src"]
EOF
```

Initialize/push:

```bash
cd "$TARGET_ROOT/harvest-flow-core"
git init
git add .
git commit -m "Initialize harvest-flow-core package"
gh repo create harvest-flow-core --public --source=. --remote=origin --push
```

## 3) Wire `harvest-flow` to depend on `harvest-flow-core`

Inside `harvest-flow` repo:

```bash
cd "$TARGET_ROOT/harvest-flow"
uv add harvest-flow-core
uv lock
git add pyproject.toml uv.lock
git commit -m "Add harvest-flow-core dependency"
git push
```

During pre-release, use git URL dependency:

```bash
uv add "harvest-flow-core @ git+https://github.com/<org>/harvest-flow-core.git"
```

## 4) Create `harvest-flow-my` (private personal instance)

```bash
mkdir -p "$TARGET_ROOT/harvest-flow-my"
rsync -a "$SRC_REPO/templates/harvest-flow-my/" "$TARGET_ROOT/harvest-flow-my/"
```

Initialize private repo:

```bash
cd "$TARGET_ROOT/harvest-flow-my"
git init
git add .
git commit -m "Initialize personal HarvestFlow instance template"
gh repo create harvest-flow-my --private --source=. --remote=origin --push
```

## 5) Personal bootstrap

```bash
cd "$TARGET_ROOT/harvest-flow-my"
cp .env.example .env
uv sync --all-extras
bash scripts/run_engine.sh
# new terminal
bash scripts/run_dashboard.sh
```

