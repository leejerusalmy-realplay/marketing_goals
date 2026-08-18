*Lee Jerusalmy*

# LS App bootstrap — provisional method compare

Launch **2026-07-16**. Scored through **2026-08-17** on LS App users with cost_date **2026-07-16..2026-08-17**.

Primary = shape so far on a fixed user set: actual `ARPU(d)/ARPU(D*)` vs candidate `ARPU_nominal(d)/ARPU_nominal(D*)`.

`native_early_rp_tail` keeps LS App native through day **30**, then dresses RP App day-to-day growth to 120.

Not a methodology lock.

## Method ranking (lower shape MAE wins)

### launch_day (16 Jul only)

| Rank | Method | Users | D* | Shape MAE | Bias |
|-----:|--------|------:|---:|----------:|-----:|
| 1 | rp_app_donor | 208 | 33 | 0.274 | 0.274 |
| 2 | hybrid_donor | 208 | 33 | 0.290 | 0.290 |
| 3 | native_early_rp_tail | 208 | 33 | 0.298 | 0.298 |
| 4 | ls_web_donor | 208 | 33 | 0.304 | 0.304 |
| 5 | native_ls_app | 208 | 33 | 0.367 | 0.367 |

### launch_week (16–22 Jul)

| Rank | Method | Users | D* | Shape MAE | Bias |
|-----:|--------|------:|---:|----------:|-----:|
| 1 | native_early_rp_tail | 2,000 | 27 | 0.083 | -0.083 |
| 2 | native_ls_app | 2,000 | 27 | 0.083 | -0.083 |
| 3 | ls_web_donor | 2,000 | 27 | 0.091 | -0.090 |
| 4 | hybrid_donor | 2,000 | 27 | 0.100 | -0.098 |
| 5 | rp_app_donor | 2,000 | 27 | 0.110 | -0.107 |

**Current leader on launch_day:** `rp_app_donor` (shape MAE 0.274).

## Frozen ARPU_nominal at checkpoints

| Method | D1 | D7 | D14 | D30 | D60 | D90 | D120 |
|--------|---:|---:|----:|----:|----:|----:|-----:|
| hybrid_donor | 4.05 | 9.86 | 13.53 | 20.23 | 30.90 | 38.69 | 43.14 |
| ls_web_donor | 4.05 | 9.75 | 14.15 | 21.39 | 34.02 | 43.42 | 48.96 |
| native_early_rp_tail | 4.05 | 12.53 | 15.64 | 24.77 | 36.06 | 44.08 | 48.45 |
| native_ls_app | 4.05 | 12.53 | 15.64 | 24.77 | 161.41 | 1051.92 | 6855.43 |
| rp_app_donor | 4.05 | 9.97 | 12.92 | 19.08 | 27.78 | 33.96 | 37.33 |

Short-horizon ranking does not see the tail. Use this table (and `plot_ls_app_horizon120.png`) for the 120-day goal.

Re-run as more post-launch cohorts accumulate.