# Quartz Style Workflow

Files:

- `custom.scss`: active overrides used by local preview/deploy sync
- `default.custom.scss`: baseline restore point (no local overrides)
- `starter.readable.scss`: safe readability preset
- `backups/custom.YYYYMMDD-HHMMSS.scss`: point-in-time snapshots

Commands:

```bash
# 1) save current active design
bash scripts/quartz-style-backup.sh

# 2) restore to fully safe baseline
bash scripts/quartz-style-restore.sh default

# 3) restore to readable starter preset
bash scripts/quartz-style-restore.sh starter

# 4) restore latest backup snapshot
bash scripts/quartz-style-restore.sh latest
```

Preview loop:

```bash
bash scripts/quartz-preview.sh
```
