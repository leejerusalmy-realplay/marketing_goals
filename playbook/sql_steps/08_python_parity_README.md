*Lee Jerusalmy*

# Step 08 — Full patch check (Python parity)

**Brands:** both use the same patch rules.  
**This fixture:** RealPrize · **Web** · one cost_date — chosen because RP Web has **winsor 1%** so pre vs post is visible.

| | RealPrize Web (fixture) | LoneStar Web (same math, different knobs) |
|--|-------------------------|---------------------------------------------|
| Winsor | **1%** → 08c pre, 08d post | **0%** → results stay like 08c |
| Tables / affids | RP | LS (swap filters if you re-write SQL) |
| CV on this single date | N/A (CV needs many dates) | same |

Full brand knobs: `CONFIG_AND_KNOBS.md`.

## Fixture

| Knob | Value |
|------|--------|
| Brand | RealPrize |
| Population | Web |
| Cost_date (cohort) | **2026-06-23** |
| Patch | **1 → 7** (every life day in the patch) |

## What “full patch” means

| Piece | Python rule | SQL day index |
|-------|-------------|----------------|
| Life day **D** | Cum with `dsi ≤ D−1` | Day 1 → dsi 0; day 7 → dsi 0…6 |
| Patch growth (CV input) | `ARPU_7 / ARPU_1` | One number for this cohort date |
| Day-steps (curve shape) | `growth_step_k = ARPU_k / ARPU_{k−1}` for k=2…7 | Six steps |
| Web winsor 1% | Cap from depositors’ cum at **e=7**, apply all days | **08d** |

Single cohort → CV does not drop this day. Still validates day formulas.

## Run order

| File | Output |
|------|--------|
| `08a_cohort_users_rp_web.sql` | N users in the cohort |
| `08b_user_cum_days_1_to_7_rp_web.sql` | Per-user cum days 1…7 |
| `08c_patch_1_to_7_full_pre_winsor_rp_web.sql` | ARPU + steps **before** winsor |
| `08d_patch_1_to_7_full_winsor1pct_rp_web.sql` | Same **after** Web winsor 1% (RP production) |

## Excel from 08b

```text
ARPU_D = SUM(cum_day_D) / n_users
growth_step_k = ARPU_k / ARPU_{k−1}
patch_growth  = ARPU_7 / ARPU_1
```

## Link to Python helpers

| Concept | Combined Python | SQL here |
|---------|-----------------|----------|
| Pre-winsor | caps ineffective / pct 0 | **08c** |
| Winsor 1% (RP Web) | `compute_winsor_caps` + `min(cum, cap_e)` | **08d** |
| User drop | Not production | 05b lab |
| Cap day | e = 7 for all columns | 08d |

See `TRIM_BY_POPULATION.md`, `CONFIG_AND_KNOBS.md`.
