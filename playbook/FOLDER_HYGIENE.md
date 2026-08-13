*Lee Jerusalmy*

# Folder hygiene — marketing_goals

Keep **Google Drive** (`lee_project/marketing_goals`) and **git** (same tree on GitHub) clean. Cursor rule: `.cursor/rules/folder-hygiene.mdc` (always on).

## Map

```
marketing_goals/
  playbook/           # durable how/why (RP + LS)
    HANDOFF.md        # ONE main agent handoff
    handoffs/         # topic handoffs only
    PIPELINE_FLOW.md, CONFIG_*, …
    sql_steps/        # Excel SQLs
  notebooks/          # working Combined scripts
    versions/         # frozen v1, v2, …
  runs/               # dated CSV exports only
  experiments/        # scratch + cv results (cache gitignored)
    cv_optimization/  # parallel CV variant Colabs + index README
  reference/          # frozen predecessors — do not edit
  config/             # yaml knobs (mirror notebook)
  src/                # future package
```

## Language

**English only** in files under `marketing_goals/` (docs, labels, comments). Chat with Lee may be Hebrew; repo content stays English.

## Defaults

| Do | Don’t |
|----|--------|
| Update HANDOFF status | New root `*HANDOFF*.md` every chat |
| `handoffs/TOPIC.md` for focused work | Scatter handoffs in playbook root |
| Merge methodology into CONFIG/PIPELINE/METHODOLOGY | Duplicate 5 files saying the same knobs |
| `runs/<as_of>_…/` for numbers | Loose CSVs at repo root |
| `notebooks/versions/` for freezes | Copy “final” notebooks next to working ones without version folder |
| Gitignore cache/parquet/gsheet | Commit 30MB parquet |

## Agent-to-agent

1. Read `playbook/HANDOFF.md` first.
2. Topic handoffs only under `playbook/handoffs/`.
3. End of session: update HANDOFF “Status / next steps” (and topic file if any).
