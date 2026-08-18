*Lee Jerusalmy*

# Did horizon-120 daily goals match Apr 10–14 reality?

**Short answer:** Blended yes (shape). Paid pops only partly — Affiliate lagged the frozen pace; dollars often missed even when shape was close. RP Web is too thin to use (65 users).

Freeze **2026-04-10**. Combined as-is (winsor / CV / lookback 35 / organic). Patches through 120 only. Actuals **not** winsorized.

**Primary:** shape — actual `ARPU(d) / ARPU(120)` vs frozen `raw_goal_ratio`.

`ARPU_nominal` is the stitched model curve **before** organic. Organic hits the ratio only (`adjusted_goal_ratio`).

### Verdict (shape, 5 dates pooled)

| Slice | Shape MAE | Read |
|-------|----------:|------|
| LS Blended | 0.018 | Stood on the goal |
| RP Blended | 0.046 | Close |
| LS Web | 0.068 | Actual paced a bit ahead |
| RP App | 0.077 | Moderate; early days slow, then caught up |
| LS Affiliate | 0.080 | Actual slower early than the frozen path |
| RP Affiliate | 0.165 | Did **not** stand on the goal (pace) |
| RP Web | 0.137 | **Ignore** — 65 users |

Level is a different sentence: LS Affiliate actual D120 ARPU was **$122 vs frozen $50**; RP Affiliate **$73 vs $26**; LS Web **$15 vs $45**. Shape can match while dollars do not.

Apr 10 vs 14 are not the same week. RP Affiliate MAE 0.21 → 0.05; LS Affiliate 0.11 → 0.18. Single-date Affiliate ARPU swings (LS Aff 13 Apr D120 = $325) — whales, not a stable daily goal.

## Overall (5 dates pooled) — shape error

| Brand | Population | Users | Shape MAE | Median AE | Bias (actual − raw) | Day-120 actual ARPU | Frozen ARPU_120 |
|-------|------------|------:|----------:|----------:|--------------------:|--------------------:|----------------:|
| lonestar | Affiliate | 5,415 | 0.080 | 0.075 | -0.080 | 122.38 | 49.77 |
| lonestar | Blended | 11,280 | 0.018 | 0.014 | 0.014 | 82.78 | 115.97 |
| lonestar | Web | 2,455 | 0.068 | 0.083 | 0.068 | 14.99 | 45.24 |
| realprize | Affiliate | 1,822 | 0.165 | 0.167 | -0.165 | 73.35 | 26.31 |
| realprize | App | 2,955 | 0.077 | 0.077 | 0.058 | 62.69 | 29.54 |
| realprize | Blended | 7,096 | 0.046 | 0.050 | -0.045 | 77.74 | 61.94 |
| realprize | Web | 65 | 0.137 | 0.129 | 0.128 | 8.61 | 1.75 |

Bias > 0 means actual pace ran **ahead** of the frozen raw path.

## Milestones — overall shape (raw vs actual ratio)

| Brand | Pop | Day | Frozen raw | Actual ratio | AE | APE | Frozen $ | Actual $ |
|-------|-----|----:|-----------:|-------------:|---:|----:|---------:|---------:|
| lonestar | Affiliate | 1 | 0.172 | 0.051 | 0.121 | 70.4% | 8.56 | 6.24 |
| lonestar | Affiliate | 7 | 0.333 | 0.139 | 0.194 | 58.1% | 16.57 | 17.07 |
| lonestar | Affiliate | 30 | 0.553 | 0.450 | 0.103 | 18.6% | 27.52 | 55.10 |
| lonestar | Affiliate | 60 | 0.726 | 0.659 | 0.068 | 9.3% | 36.16 | 80.62 |
| lonestar | Affiliate | 90 | 0.878 | 0.839 | 0.040 | 4.5% | 43.72 | 102.65 |
| lonestar | Affiliate | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 49.77 | 122.38 |
| lonestar | Blended | 1 | 0.072 | 0.063 | 0.008 | 11.4% | 8.30 | 5.25 |
| lonestar | Blended | 7 | 0.191 | 0.160 | 0.031 | 16.1% | 22.14 | 13.26 |
| lonestar | Blended | 30 | 0.407 | 0.454 | 0.047 | 11.6% | 47.21 | 37.59 |
| lonestar | Blended | 60 | 0.619 | 0.646 | 0.027 | 4.3% | 71.83 | 53.47 |
| lonestar | Blended | 90 | 0.834 | 0.834 | 0.001 | 0.1% | 96.76 | 69.00 |
| lonestar | Blended | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 115.97 | 82.78 |
| lonestar | Web | 1 | 0.090 | 0.126 | 0.036 | 40.5% | 4.07 | 1.89 |
| lonestar | Web | 7 | 0.232 | 0.300 | 0.068 | 29.5% | 10.48 | 4.50 |
| lonestar | Web | 30 | 0.444 | 0.549 | 0.104 | 23.4% | 20.11 | 8.22 |
| lonestar | Web | 60 | 0.620 | 0.728 | 0.108 | 17.4% | 28.05 | 10.92 |
| lonestar | Web | 90 | 0.809 | 0.861 | 0.052 | 6.5% | 36.61 | 12.92 |
| lonestar | Web | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 45.24 | 14.99 |
| realprize | Affiliate | 1 | 0.235 | 0.099 | 0.136 | 57.7% | 6.19 | 7.30 |
| realprize | Affiliate | 7 | 0.388 | 0.195 | 0.193 | 49.7% | 10.20 | 14.30 |
| realprize | Affiliate | 30 | 0.587 | 0.422 | 0.166 | 28.2% | 15.45 | 30.93 |
| realprize | Affiliate | 60 | 0.750 | 0.567 | 0.183 | 24.4% | 19.74 | 41.60 |
| realprize | Affiliate | 90 | 0.900 | 0.739 | 0.161 | 17.9% | 23.66 | 54.18 |
| realprize | Affiliate | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 26.31 | 73.35 |
| realprize | App | 1 | 0.129 | 0.033 | 0.096 | 74.5% | 3.80 | 2.05 |
| realprize | App | 7 | 0.271 | 0.194 | 0.077 | 28.4% | 8.02 | 12.17 |
| realprize | App | 30 | 0.514 | 0.590 | 0.075 | 14.7% | 15.20 | 36.97 |
| realprize | App | 60 | 0.691 | 0.810 | 0.119 | 17.2% | 20.42 | 50.77 |
| realprize | App | 90 | 0.841 | 0.923 | 0.081 | 9.7% | 24.85 | 57.83 |
| realprize | App | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 29.54 | 62.69 |
| realprize | Blended | 1 | 0.097 | 0.051 | 0.046 | 47.9% | 6.01 | 3.93 |
| realprize | Blended | 7 | 0.226 | 0.179 | 0.047 | 20.8% | 13.98 | 13.89 |
| realprize | Blended | 30 | 0.456 | 0.434 | 0.022 | 4.9% | 28.27 | 33.74 |
| realprize | Blended | 60 | 0.674 | 0.623 | 0.050 | 7.5% | 41.74 | 48.47 |
| realprize | Blended | 90 | 0.843 | 0.791 | 0.053 | 6.2% | 52.23 | 61.46 |
| realprize | Blended | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 61.94 | 77.74 |
| realprize | Web | 1 | 0.244 | 0.104 | 0.141 | 57.6% | 0.43 | 0.89 |
| realprize | Web | 7 | 0.401 | 0.371 | 0.029 | 7.3% | 0.70 | 3.20 |
| realprize | Web | 30 | 0.566 | 0.834 | 0.268 | 47.3% | 0.99 | 7.18 |
| realprize | Web | 60 | 0.707 | 0.870 | 0.163 | 23.1% | 1.23 | 7.49 |
| realprize | Web | 90 | 0.895 | 0.982 | 0.087 | 9.8% | 1.56 | 8.46 |
| realprize | Web | 120 | 1.000 | 1.000 | 0.000 | 0.0% | 1.75 | 8.61 |

## 10 Apr vs 14 Apr — shape MAE vs the same frozen path

| Brand | Population | 10 Apr MAE | 14 Apr MAE | 10 Apr bias | 14 Apr bias |
|-------|------------|-----------:|-----------:|------------:|------------:|
| lonestar | Affiliate | 0.107 | 0.175 | -0.107 | -0.174 |
| lonestar | Blended | 0.012 | 0.058 | -0.006 | -0.026 |
| lonestar | Web | 0.066 | 0.044 | 0.055 | -0.014 |
| realprize | Affiliate | 0.208 | 0.054 | -0.208 | -0.042 |
| realprize | App | 0.107 | 0.031 | -0.073 | 0.002 |
| realprize | Blended | 0.070 | 0.028 | -0.069 | 0.004 |
| realprize | Web | 0.077 | 0.166 | -0.045 | 0.159 |

## How to read this

- **Shape (primary):** did the realized *pace* to day 120 match the frozen raw path?
- **Level:** same shape can still miss dollars (`actual ARPU` vs `ARPU_nominal`).
- **Adjusted:** sits below the actual ratio by ~organic, by design. Not the verdict.
- Actuals include $0 users in N. No fill of missing days.

Not a methodology lock.
