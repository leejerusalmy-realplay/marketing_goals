# Playbook

How to understand and (later) re-run marketing goals.

## Documents here

| File | What |
|------|------|
| `HANDOFF.md` | **Start here** in a new chat — status, next steps, locked understanding |
| `LS_PIPELINE_FLOW.md` | Full LS chart pipeline + Q&A (includes curve tail / `is_extrapolated`) |
| `METHODOLOGY.md` | What we calculate and why (formula, data sources, trim, organic, goals) |
| `DECISIONS.md` | Dated locks (trim %, organic cap, etc.) as we decide them |
| `sql_steps/` | One SQL per calculation for BigQuery → Excel checks |

## Learning order

1. Combined RealPrize methodology (this playbook + `reference/…Combined_RealPrize.ipynb`)
2. LoneStar diffs (no App yet; different affid list; two-pass curve)
3. Organic Share and TrimComparison labs when tuning knobs

## Verification rule

For every calculation: explain → runnable SQL in `sql_steps/` → Lee checks in Excel → only then trust the next step.
