# Step B: Personal Repository Split Checklist

1. Create private `harvest-flow-my` repository.
2. Start from `templates/harvest-flow-my/` as the base template.
3. Copy personal files listed in `MIGRATION/PRIVATE_MANIFEST.yaml`.
4. Keep personal `.env` and deployment secrets private.
5. Install core/open-source package dependency:
   - `uv add harvest-flow` (or git URL during pre-release).
6. Run:
   - `uv run harvest-flow-engine`
   - `uv run harvest-flow-dashboard`
7. Verify blog deploy workflow in personal repository.
8. Optional: follow `MIGRATION/REPO_SPLIT_COMMANDS.md` for end-to-end split command sequence.

