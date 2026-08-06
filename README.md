# Marketing Goals

Build day-by-day deposit ARPU goals by acquisition population (Web / App / Affiliate / Blended), adjusted for organic share.

**Owner:** Lee Jerusalmy  
**Repo:** https://github.com/leejerusalmy-realplay/marketing_goals

## Folder roles

| Folder | Role |
|--------|------|
| `reference/` | Frozen predecessor notebooks — **do not edit** |
| `playbook/` | Instruction manual + methodology + Excel-check SQL steps |
| `config/` | Knobs per brand (dates, trim, populations, affid maps) |
| `src/` | Shared Python helpers (filled in as we rebuild) |
| `notebooks/` | Clean runnable notebooks (filled in as we rebuild) |
| `runs/` | Dated output CSVs from a specific run — never overwrite |

## How we work (simple)

1. Learn and verify each calculation with SQL → Excel (see `playbook/`).
2. Rebuild cleanly into `src/` + `notebooks/` when ready.
3. Change settings in `config/`, run, save outputs under `runs/<date>_<brand>/`.
4. Say **“save a version”** to snapshot to GitHub; **“go back to …”** to restore.

## Current phase

**Rebuild started.** Unified Colab: `notebooks/Marketing_Goals_Combined_RP_LS.ipynb` (RP + LS → one goals table). Numbers still need parity check vs frozen `reference/` Combined notebooks before production use.

**New chat?** Start the agent on `playbook/HANDOFF.md`.
