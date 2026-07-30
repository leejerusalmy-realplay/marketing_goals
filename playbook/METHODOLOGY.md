# Methodology (from predecessor Combined notebooks)

Status: **draft from reference code** — not yet Excel-verified step by step.

## What the deliverable is

For each population and goal horizon (7, 30, 60, …, 365 days), a day-by-day **goal ratio**: what share of horizon ARPU should deposits have reached by day *d*.

### Core formula

**Per population (Web / App / Affiliate):**

`adjusted_goal = (ARPU_day / ARPU_horizon) × (1 − organic_share_at_horizon)`

**Blended (all users in one bucket):**

`adjusted_goal = ARPU_day / ARPU_horizon`  
(no organic adjustment)

Within a horizon, organic share is taken at the **horizon endpoint** (constant for every day inside that horizon) — marketing-team rule in the predecessor code.

## Data sources

| Need | Table |
|------|--------|
| Users, cost date, affid / population | `analytics.realprize_cost_per_user` or `analytics.lonestar_cost_per_user` |
| Deposits | `{brand}.casino_astropay_dmn` where `Status = 'APPROVED'`; amount `/ 100` |

Notes from predecessor:

- Cost-per-user tables are already filtered `test_account = 0` and `marketing_account = 0`.
- TikTok affid `4313` excluded.
- PPC is included in organic-share denominator but **not** in per-population ARPU curve populations.

## Populations (affid → label)

See `config/realprize.yaml` and `config/lonestar.yaml`.

## Pipeline steps (high level)

1. Assign each user a population + first `cost_date` (cohort date).
2. Attach deposits; compute days-since-install (`dsi`) and cumulative revenue per user.
3. Build ARPU growth in **patches** (e.g. day 1→7, 7→14, … 270→365).
4. Apply **trim** (winsor or cohort_trim); **persistent** = once excluded, stay excluded later.
5. Adaptive **CV** cleanup: drop outlier cohort dates until growth CV is stable enough.
6. Stitch patches into a full-day ARPU curve.
7. Compute **organic share** by scope × horizon.
8. Build **goals** from curve + organic share.

## Open items to verify in Excel

- [ ] Population assignment counts vs affid lists
- [ ] First cost_date definition
- [ ] Cumulative revenue / dsi
- [ ] Winsor vs cohort_trim math
- [ ] Persistent trim carry-forward
- [ ] CV date removal
- [ ] Organic share (RP app vs non_app; share cap at day 120)
- [ ] Final goal ratio

SQL for each checkbox will live under `playbook/sql_steps/` as we go.
