*Lee Jerusalmy*

# Freeze 2026-07-10 vs available actuals through 2026-08-17 (winsor_esc)

Goals frozen at **2026-07-10**. Scored on life days we already have (oldest cohort = **39** days). Actuals not winsorized.

**Primary:** shape so far on `first_day` (10 Jul only, same N every day): actual `ARPU(d)/ARPU(39)` vs frozen `ARPU_nominal(d)/ARPU_nominal(39)`.

`first_5_days` (10–14 Jul) is the April-style 5-day wave (D* = 35). `overall_level` is dollars only — N changes by day, do not use for shape.

## first_day (10 Jul) — shape so far

| Brand | Population | Users | D* | Shape MAE | Bias | Day-D* actual $ | Frozen $ at D* |
|-------|------------|------:|---:|----------:|-----:|----------------:|---------------:|
| lonestar | Affiliate | 943 | 39 | 0.050 | 0.040 | 20.36 | 15.60 |
| lonestar | Blended | 2,040 | 39 | 0.038 | 0.015 | 63.02 | 41.13 |
| lonestar | Web | 594 | 39 | 0.061 | 0.005 | 141.83 | 32.61 |
| realprize | Affiliate | 321 | 39 | 0.142 | 0.010 | 127.83 | 13.14 |
| realprize | App | 764 | 39 | 0.122 | 0.121 | 83.06 | 19.20 |
| realprize | Blended | 1,690 | 39 | 0.135 | 0.135 | 81.09 | 28.02 |
| realprize | Web | 133 | 39 | 0.041 | 0.021 | 16.41 | 5.59 |

Bias > 0 means actual pace ran **ahead** of the frozen path (to D*).

Not a methodology lock.
