# Release Promotion Playbook (core -> app -> my)

## Promotion Order (Mandatory)
1. `harvest-flow-core`
2. `harvest-flow`
3. `harvest-flow-my` (or personal fork such as `harvest-flow-mscsy0104-notes`)

Do not skip or reorder steps. Each stage requires evidence from the previous one.

## Gate Ownership

- **Core maintainer (tag owner)**  
  - Creates and signs core version tags.
  - Publishes release notes with API change classification (`breaking` / `non-breaking`).
  - Confirms core unit CI is green.

- **App maintainer (compat owner)**  
  - Updates app core range and verifies no private core imports.
  - Runs app lint/tests and adapter/integration smoke.
  - Confirms app CI is green against latest allowed core.

- **Ops maintainer (personal owner)**  
  - Pins promoted app/core versions in personal repo.
  - Executes personal smoke runbook (engine + dashboard + one note flow).
  - Records rollback-ready previous version pins.

## Rollback Playbook (Reverse Order)

Rollback only if needed and only in this order:
1. Revert/pin down `harvest-flow-my` to last known good app/core versions.
2. Revert `harvest-flow` compatibility bump or release tag.
3. Revert `harvest-flow-core` release only for confirmed core regression.

If app smoke fails after core release, prefer app hotfix first; core rollback is last resort.

## Required Evidence Per Gate

- **Gate 1 (Core Ready):** core API export check + unit CI + release candidate note.
- **Gate 2 (App Ready):** compatible core range update + boundary safeguard test + app CI/smoke.
- **Gate 3 (Ops Ready):** personal pin/update note + personal smoke runbook result.
- **Gate 4 (Merge/Release):** merge and tag confirmations in the fixed promotion order.
