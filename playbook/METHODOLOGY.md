# Methodology (from predecessor Combined notebooks)

Status: **draft from reference code** — not yet Excel-verified step by step.

## Time & cost discipline

Important for every query and script in this project: **save time and money** while still being correct and Excel-checkable.

- Prefer **small, step-sized SQL** for learning checks — not full-history mega-pulls into pandas.
- Use a **tight date window** and/or **LIMIT / sample** when verifying logic in Excel; widen only when the step is proven.
- Avoid re-scanning the same huge tables repeatedly; reuse cached extracts or write intermediate results once when useful.
- Don’t pull columns or populations you don’t need for the current step.
- Heavy Colab loops over all users × many trim variants (e.g. Blended TrimComparison) are expensive in **runtime**; treat them as occasional calibration, not daily exploration.
- When suggesting SQL/scripts, call out if a query is likely **expensive** (bytes scanned / long runtime) and offer a cheaper check variant first.

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

- [x] Population assignment counts vs affid lists *(Step 01)*
- [x] First cost_date definition / always cost_date not dateReg *(Step 01–02)*
- [x] Cumulative revenue / dsi *(Step 02)*
- [x] Cohort ARPU + day-D uses dsi ≤ D−1 *(Step 03)*
- [ ] Patch growth ratio ARPU_e / ARPU_s *(Step 04)*
- [ ] Winsor vs cohort_trim math
- [ ] Persistent trim carry-forward
- [ ] CV date removal
- [ ] Organic share (RP app vs non_app; share cap at day 120)
- [ ] Final goal ratio

SQL for each checkbox will live under `playbook/sql_steps/` as we go.
