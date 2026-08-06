*Lee Jerusalmy*

# Methodology (from predecessor Combined notebooks)

Status: **production coded** in unified Combined notebooks; Excel-verify still step-by-step for some boxes.  
Knob reference: **`CONFIG_AND_KNOBS.md`**. Trim map: **`TRIM_BY_POPULATION.md`**.

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

Locked columns: `brand`, `population`, `goal_horizon`, `day`, `raw_goal_ratio`, `organic_share`, `adjusted_goal_ratio`.

## Data sources

| Need | Table |
|------|--------|
| Users, cost date, affid / population | `analytics.realprize_cost_per_user` or `analytics.lonestar_cost_per_user` |
| Deposits | `{brand}.casino_astropay_dmn` where `Status = 'APPROVED'`; amount `/ 100` |

Notes from predecessor:

- Cost-per-user tables are already filtered `test_account = 0` and `marketing_account = 0`.
- RP excludes TikTok affid `4313`; LS excludes `4866`, `7127`.
- PPC is included in organic-share denominator but **not** in per-population ARPU curve populations.
- Filter `id > 0` (test/negatives).

## Populations (affid → label)

See `config/realprize.yaml` and `config/lonestar.yaml` + Combined `BRAND_CONFIGS`.

### User columns for organic share

| Brand | SQL columns | Organic world |
|-------|-------------|----------------|
| **RP** | population + **scope** (app/non_app) + **bucket** (organic/acquired) | Share split by scope; Web goals use non_app |
| **LS** | population + cost_date only | Helper sets scope=`all`; bucket from Organic population |

Detail: `CONFIG_AND_KNOBS.md` § “User structure”.

## Pipeline steps (high level)

1. Assign each user a population + first `cost_date` (cohort date). Optional RP scope/bucket.
2. Attach deposits; compute dsi and cumulative revenue per user. Day **D** = dsi ≤ D−1.
3. For each **patch** (s→e) and population: mature lookback of ~35 cost_dates.
4. Apply **winsor** (production) at patch end e: cap whale $; keep N. (cohort_trim = labs only.)
5. Adaptive **CV** cleanup: drop outlier **cost_dates** until CV ≤ 0.10 or hit 15% remove cap. Flag if still above brand threshold (RP 0.15 / LS 0.175).
6. Gate: if cost_dates left &lt; `min_cohort_dates` (RP=1, LS=20) → skip patch.
7. Weighted day-to-day growth steps on kept dates → stitch full ARPU curve.
   - Optional **LS** only: if last real day &lt; 365, **extend** with geometric mean of last ~30 steps → `is_extrapolated = True`. See `LS_PIPELINE_FLOW.md` Box 11.
8. Compute **organic share** by scope × horizon (LS: scope all). RP pin lookup at horizon min(H, 120).
9. Build **goals** from curve + organic share (ratios only; extrapolation flag audit-only).

### Trim vs CV vs min_cohort_dates (don’t mix)

| Layer | Removes? | Unit |
|-------|----------|------|
| Winsor | Dollars above cap | Per user cum |
| Cohort_trim | Users (labs) | Per user |
| Adaptive CV | Noisy **cost_dates** | Per patch |
| min_cohort_dates | Whole **patch** if too few dates left | Patch skip |

## Open items to verify in Excel

- [x] Population assignment counts vs affid lists *(Step 01)*
- [x] First cost_date definition / always cost_date not dateReg *(Step 01–02)*
- [x] Cumulative revenue / dsi *(Step 02)*
- [x] Cohort ARPU + day-D uses dsi ≤ D−1 *(Step 03)*
- [ ] Patch growth ratio ARPU_e / ARPU_s *(Step 04; step 08 parity in progress)*
- [ ] Winsor math (pre/post 08c vs 08d)
- [ ] Persistent trim carry-forward *(only bites if cohort_trim used)*
- [ ] CV date removal
- [ ] Organic share (RP app vs non_app; share cap at day 120)
- [ ] Final goal ratio *(Step 07 SQL ready — Excel lock pending)*
- [ ] min_cohort_dates skip behavior (LS 20)

SQL for each checkbox lives under `playbook/sql_steps/`.
