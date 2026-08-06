# Step 08 — Full patch check (Python parity)

## Fixture

| Knob | Value |
|------|--------|
| Brand | RealPrize |
| Population | Web |
| Cost_date (cohort) | **2026-06-23** |
| Patch | **1 → 7** (full: every life day in the patch) |

## What “full patch” means

| Piece | Python rule | SQL day index |
|-------|-------------|----------------|
| Life day **D** | Cum deposits with `dsi ≤ D−1` | Day 1 → dsi 0; day 7 → dsi 0…6 |
| Patch growth (CV input) | `ARPU_7 / ARPU_1` | One number for this cohort date |
| Day-steps (curve shape) | `growth_step_k = ARPU_k / ARPU_{k−1}` for k=2…7 | Six steps |
| Web winsor 1% | Cap from **depositors’** cum at patch **end e=7**, apply to all day cums | **08d** |

Single cohort → CV does not drop this day (CV ranks *across* many cost_dates). Still validates every day formula for this date.

## Run order

| File | Output |
|------|--------|
| `08a_cohort_users_rp_web.sql` | N users in the cohort |
| `08b_user_cum_days_1_to_7_rp_web.sql` | Per-user cum for days **1…7** (Excel ground truth) |
| `08c_patch_1_to_7_full_pre_winsor_rp_web.sql` | ARPU_1…7, day-steps 2…7, growth 1→7 **before** winsor |
| `08d_patch_1_to_7_full_winsor1pct_rp_web.sql` | Same **after** Web winsor 1% (production) |

## Excel from 08b

For each day D in 1…7:

```text
ARPU_D = SUM(cum_day_D) / n_users
```

Day-steps:

```text
growth_step_2 = ARPU_2 / ARPU_1
…
growth_step_7 = ARPU_7 / ARPU_6
patch_growth  = ARPU_7 / ARPU_1
```

08c/08d must match those sums. 08d should be what Combined uses for this cost_date after caps.

## Link to Python “trim helpers”

| Concept | Combined Python | SQL here |
|---------|-----------------|----------|
| Pre-winsor ARPU / growth | `sum_cum_at_idx` without effective caps (pct 0) | **08c** |
| Winsor 1% (RP Web) | `compute_winsor_caps` + `min(cum, cap_e)` in `sum_cum_at_idx` | **08d** |
| User drop | **Not** on production Web — method is winsor | n/a (see 05b for cohort_trim lab) |
| Cap day | Patch end **e = 7** for all day columns | 08d builds `cap_e` from c7 |

See `playbook/TRIM_BY_POPULATION.md` and `playbook/CONFIG_AND_KNOBS.md`.
