*Lee Jerusalmy*

# handoffs/ — agent handoffs (topic-specific)

## Rule

| File | When |
|------|------|
| **`../HANDOFF.md`** | **Always first.** Main project status, locks, next steps for any new agent chat. |
| Files in **this folder** | Only when starting a **narrow** workstream (e.g. CV experiment). Read main HANDOFF first, then the topic file. |

## Naming

`TOPIC_SHORT_NAME.md` — one active focus per file.  
When a workstream is done, leave the file as archive or mark it done in the header; do not delete without Lee’s OK.

## Index

| File | Topic | Status |
|------|--------|--------|
| `CV_OPTIMIZATION.md` | CV optimization — next stage: `cv_oos_backtest` (does high CV hurt goal reliability?) | **Next chat focus** — updated 2026-08-13 |

## How agents create a new handoff

1. Add `playbook/handoffs/<TOPIC>.md` (do **not** create another main HANDOFF at playbook root).
2. Link it from the table above.
3. Point “start” paste to: read `playbook/HANDOFF.md` then this file.
4. When session ends: update **Status / next steps** in that topic file *and* main `HANDOFF.md` if project-wide.
