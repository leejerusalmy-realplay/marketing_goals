*Lee Jerusalmy*

# Playbook

How to understand and (later) re-run marketing goals.

## Documents here

| File | What |
|------|------|
| `HANDOFF.md` | **Start here** in a new chat — status, next steps, locked understanding |
| `CONFIG_AND_KNOBS.md` | **Config cell**: patches, brand knobs, min_cohort_dates, scope/bucket, seed globals, where winsor is chosen/applied |
| `TRIM_BY_POPULATION.md` | Per-pop winsor map; winsor vs cohort_trim; code paths |
| `LS_PIPELINE_FLOW.md` | Full LS chart pipeline + Q&A (includes curve tail / `is_extrapolated`) |
| Google Doc | Plain-language LS guide: https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit |
| `METHODOLOGY.md` | What we calculate and why (formula, data sources, trim, organic, goals) |
| `WORKED_EXAMPLE_RP_WEB.md` | Numeric RP Web walkthrough |
| `DECISIONS.md` | Dated locks (trim %, organic cap, etc.) as we decide them |
| `sql_steps/` | One SQL per calculation for BigQuery → Excel checks |

## Learning order

1. `CONFIG_AND_KNOBS.md` + `TRIM_BY_POPULATION.md` (how knobs work)
2. Combined RP methodology (`METHODOLOGY.md` + `WORKED_EXAMPLE_RP_WEB.md` + Google Doc / `LS_PIPELINE_FLOW.md`)
3. LoneStar diffs (no App; different affid / CV / min_cohort / tail; scope=all)
4. Excel SQL in `sql_steps/` (01 → 08 full patch)
5. Organic Share and TrimComparison labs when tuning knobs

## Verification rule

For every calculation: explain → runnable SQL in `sql_steps/` → Lee checks in Excel → only then trust the next step.
