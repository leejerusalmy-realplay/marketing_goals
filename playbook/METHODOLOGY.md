*Lee Jerusalmy*

# Methodology — RealPrize + LoneStar

**Brands:** both. Same pipeline math. Knobs differ by brand (tables below).  
**Knob master:** `CONFIG_AND_KNOBS.md` · **Step-by-step:** `PIPELINE_FLOW.md`

Status: coded in unified Combined notebooks; Excel-verify ongoing.

---

## Shared vs different (start here)

### Same for both brands

- Day **D** uses deposits with **dsi ≤ D−1**; cohort clock = **cost_date**
- Patches, lookback 35, horizons 7…365, goals formula shape
- Winsor method (not cohort_trim) in production; cap at patch end **e**; users stay in N
- CV: weighted σ/μ on patch growth; stop at 0.10; max remove 15% of cost_dates
- Organic share measured at **horizon end**; constant for every day inside that horizon
- Blended goals: no organic haircut (`organic_share = 0`)
- Deliverable columns: `brand`, `population`, `goal_horizon`, `day`, `raw_goal_ratio`, `organic_share`, `adjusted_goal_ratio`

### Different by brand

| Area | RealPrize | LoneStar |
|------|-----------|----------|
| Tables | `analytics.realprize_cost_per_user`, `realprize.casino_astropay_dmn` | `analytics.lonestar_cost_per_user`, `lonestar.casino_astropay_dmn` |
| Drop affids | 4313 | 4866, 7127 |
| Curve pops | Web, **App**, Affiliate + Blended | Web, Affiliate + Blended (**no App**) |
| Web winsor | **1%** | **0%** |
| App / Aff / Blended winsor | 0% / **1%** / 0% | n/a / **1%** / 0% |
| CV flag after cleanup | **0.15** | **0.175** |
| min_cohort_dates | **1** | **20** |
| Organic user shape | scope app/non_app + bucket | scope **all** (no columns) |
| Organic pin | horizons **>120** use D120 share | no pin |
| Curve tail fill | off | on (~30 day-steps) → `is_extrapolated` |
| Web affid list | 63, 2521, 2535, 4957, 4971, 5048, 5062, 5069 | 63, 4432, 4551, 4698, 5048, 5125, 7120, 7253, 7260, 8331, 8345 |
| Organic affids | 0, 78, **2290** | 0, 78 |

Config lives in notebook `BRAND_CONFIGS` (+ `config/realprize.yaml` / `config/lonestar.yaml` mirrors).

---

## Time & cost discipline

- Prefer **small, step-sized SQL** for learning checks — not full-history mega-pulls.
- Tight date window and/or sample when verifying in Excel.
- Don’t re-scan huge tables; reuse extracts when useful.
- Flag expensive BQ jobs; offer a cheaper check first.

---

## What the deliverable is

For each brand, population, and goal horizon (7…365), day-by-day **goal ratio**: share of horizon ARPU reached by day *d*.

### Core formula

**Per population (Web / App / Affiliate):**

`adjusted_goal = (ARPU_day / ARPU_horizon) × (1 − organic_share_at_horizon)`

**Blended:**

`adjusted_goal = ARPU_day / ARPU_horizon`  
(no organic adjustment)

Organic share = value at horizon **endpoint** (not per mid-horizon day).

---

## Data sources by brand

| Need | RealPrize | LoneStar |
|------|-----------|----------|
| Users / cost_date | `analytics.realprize_cost_per_user` | `analytics.lonestar_cost_per_user` |
| Deposits | `realprize.casino_astropay_dmn` | `lonestar.casino_astropay_dmn` |

Shared rules: `Status = 'APPROVED'`, amount `/ 100`, `id > 0`, cost tables already drop test/marketing.

---

## Pipeline steps (high level)

Both brands walk the same boxes. Brand knobs applied via `apply_brand_globals` before each brand run.

1. Assign population + first `cost_date`. **RP** also sets scope/bucket columns.
2. Attach deposits → dsi → cumulative revenue. Day D = dsi ≤ D−1.
3. For each patch s→e: mature ~35 cost_dates.
4. Winsor at e (population pct from brand trim_config).
5. Adaptive CV on cost_dates (stop 0.10; flag if still > brand threshold).
6. If dates left &lt; min_cohort_dates → skip patch (**RP 1 / LS 20**).
7. Day-to-day weighted steps → stitch curve. **LS only:** optional tail fill to 365.
8. Organic share by scope × horizon. **RP:** pin lookup at min(H, 120). **LS:** scope=all.
9. Goals from curve + organic.

### Layers (don’t mix)

| Layer | What it drops | Same for both? |
|-------|---------------|----------------|
| Winsor | $ over cap | Method yes; **pct differs by pop** |
| Cohort_trim | Users | Labs only, both brands |
| CV | Noisy cost_dates | Stop/remove fraction same; **flag line differs** |
| min_cohort_dates | Whole patch | **1 vs 20** |

---

## Open Excel items

| Topic | Notes |
|-------|--------|
| Population / id>0 | RP locked (DECISIONS); LS same rule |
| dsi / day D | Shared |
| Patch / winsor | SQL 04–05 + 08 (RP Web fixture); extend LS later |
| CV | Shared logic; thresholds differ |
| Organic | RP non_app + cap 120; LS all |
| Goals formula | Step 07 toy; brand-independent math |

SQL: `playbook/sql_steps/`.
