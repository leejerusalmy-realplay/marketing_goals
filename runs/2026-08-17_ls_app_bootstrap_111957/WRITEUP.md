*Lee Jerusalmy*

# LS App bootstrap — provisional method compare

Launch **2026-07-16**. Scored through **2026-08-17** on LS App users with cost_date **2026-07-16..2026-08-17**.

Primary = shape so far on a fixed user set: actual `ARPU(d)/ARPU(D*)` vs candidate `ARPU_nominal(d)/ARPU_nominal(D*)`.

Not a methodology lock.

## Method ranking (lower shape MAE wins)

### launch_day (16 Jul only)

| Rank | Method | Users | D* | Shape MAE | Bias |
|-----:|--------|------:|---:|----------:|-----:|
| 1 | rp_app_donor | 208 | 33 | 0.274 | 0.274 |
| 2 | hybrid_donor | 208 | 33 | 0.290 | 0.290 |
| 3 | ls_web_donor | 208 | 33 | 0.304 | 0.304 |
| 4 | native_ls_app | 208 | 33 | 0.367 | 0.367 |

### launch_week (16–22 Jul)

| Rank | Method | Users | D* | Shape MAE | Bias |
|-----:|--------|------:|---:|----------:|-----:|
| 1 | native_ls_app | 2,000 | 27 | 0.083 | -0.083 |
| 2 | ls_web_donor | 2,000 | 27 | 0.091 | -0.090 |
| 3 | hybrid_donor | 2,000 | 27 | 0.100 | -0.098 |
| 4 | rp_app_donor | 2,000 | 27 | 0.110 | -0.107 |

**Current leader on launch_day:** `rp_app_donor` (shape MAE 0.274).

Re-run as more post-launch cohorts accumulate.