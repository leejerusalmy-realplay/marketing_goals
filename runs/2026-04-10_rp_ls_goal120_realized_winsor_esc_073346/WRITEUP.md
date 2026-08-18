*Lee Jerusalmy*

# Did capped winsor_escalation H=120 goals match Apr 10–14 better?

Same freeze as the production Combined check: **2026-04-10**, eval cost_dates **Apr 10–14**, actuals **not** winsorized, primary = **shape**.

Frozen goals from **capped** `winsor_escalation` (stop if revenue cut > **15%** absolute). `pct_used` is wired into curve day-steps for this check only — without that, goals would still sit on floor winsor and the comparison would be empty.

Not a methodology lock. Does not change generic Combined.

## Overall (5 dates pooled) — shape error, this engine

| Brand | Population | Users | Shape MAE | Median AE | Bias (actual − raw) | Day-120 actual ARPU | Frozen ARPU_120 |
|-------|------------|------:|----------:|----------:|--------------------:|--------------------:|----------------:|
| lonestar | Affiliate | 5,415 | 0.080 | 0.075 | -0.080 | 122.38 | 49.77 |
| lonestar | Blended | 11,280 | 0.018 | 0.014 | 0.014 | 82.78 | 101.03 |
| lonestar | Web | 2,455 | 0.051 | 0.059 | 0.051 | 14.99 | 36.66 |
| realprize | Affiliate | 1,822 | 0.165 | 0.167 | -0.165 | 73.35 | 26.31 |
| realprize | App | 2,955 | 0.077 | 0.084 | 0.043 | 62.69 | 23.92 |
| realprize | Blended | 7,096 | 0.046 | 0.050 | -0.045 | 77.74 | 51.80 |
| realprize | Web | 65 | 0.132 | 0.128 | 0.118 | 8.61 | 1.59 |

## Which engine matches better? (primary = shape MAE, overall)

Production freeze: `runs/2026-04-10_rp_ls_goal120_realized_133457`.

| Brand | Pop | Users | Prod MAE | Esc MAE | Δ (esc − prod) | Winner | Prod ARPU_120 | Esc ARPU_120 |
|-------|-----|------:|---------:|--------:|---------------:|--------|--------------:|-------------:|
| lonestar | Affiliate | 5,415 | 0.080 | 0.080 | 0.000 | tie | 49.77 | 49.77 |
| lonestar | Blended | 11,280 | 0.018 | 0.018 | 0.000 | production | 115.97 | 101.03 |
| lonestar | Web | 2,455 | 0.068 | 0.051 | -0.017 | winsor_esc | 45.24 | 36.66 |
| realprize | Affiliate | 1,822 | 0.165 | 0.165 | 0.000 | tie | 26.31 | 26.31 |
| realprize | App | 2,955 | 0.077 | 0.077 | 0.000 | production | 29.54 | 23.92 |
| realprize | Blended | 7,096 | 0.046 | 0.046 | 0.000 | production | 61.94 | 51.80 |
| realprize | Web | 65 | 0.137 | 0.132 | -0.004 | winsor_esc | 1.75 | 1.59 |

Lower shape MAE = closer pace to realized `ARPU(d)/ARPU(120)`. RP Web is thin (ignore). Affiliate floor 1% already cuts a large $ share, so those patches can show `capped_by_revenue_limit` even without climbing the ladder.

## Freeze-T CV / winsor (patches through 120)

| brand | population | patch | floor_pct | pct_used | escalated | revenue_cut_fraction | capped_by_revenue_limit | cv_before | cv_after | flagged |
|---|---|---|---|---|---|---|---|---|---|---|
| realprize | Web | 1->7 | 0.010 | 0.050 | True | 0.030 | False | 0.735 | 0.283 | True |
| realprize | Web | 7->14 | 0.010 | 0.050 | True | 0.050 | False | 0.355 | 0.159 | True |
| realprize | Web | 14->30 | 0.010 | 0.050 | True | 0.110 | False | 0.524 | 0.185 | True |
| realprize | Web | 30->60 | 0.010 | 0.050 | True | 0.140 | False | 0.248 | 0.146 | False |
| realprize | Web | 60->90 | 0.010 | 0.010 | False | 0.202 | True | 0.188 | 0.129 | False |
| realprize | Web | 90->120 | 0.010 | 0.010 | False | 0.266 | True | 0.180 | 0.086 | False |
| realprize | App | 1->7 | 0.000 | 0.005 | True | 0.075 | True | 0.426 | 0.263 | True |
| realprize | App | 7->14 | 0.000 | 0.005 | True | 0.085 | False | 0.176 | 0.114 | False |
| realprize | App | 14->30 | 0.000 | 0.005 | True | 0.088 | True | 0.435 | 0.175 | True |
| realprize | App | 30->60 | 0.000 | 0.005 | True | 0.086 | False | 0.249 | 0.148 | False |
| realprize | App | 60->90 | 0.000 | 0.000 | False | 0.000 | False | 0.180 | 0.134 | False |
| realprize | App | 90->120 | 0.000 | 0.000 | False | 0.000 | False | 0.124 | 0.106 | False |
| realprize | Affiliate | 1->7 | 0.010 | 0.010 | False | 0.300 | True | 0.433 | 0.156 | True |
| realprize | Affiliate | 7->14 | 0.010 | 0.010 | False | 0.318 | True | 0.132 | 0.091 | False |
| realprize | Affiliate | 14->30 | 0.010 | 0.010 | False | 0.323 | True | 0.138 | 0.099 | False |
| realprize | Affiliate | 30->60 | 0.010 | 0.010 | False | 0.414 | True | 0.127 | 0.098 | False |
| realprize | Affiliate | 60->90 | 0.010 | 0.010 | False | 0.262 | True | 0.124 | 0.087 | False |
| realprize | Affiliate | 90->120 | 0.010 | 0.010 | False | 0.290 | True | 0.102 | 0.073 | False |
| realprize | Blended | 1->7 | 0.000 | 0.005 | True | 0.148 | False | 0.240 | 0.143 | False |
| realprize | Blended | 7->14 | 0.000 | 0.000 | False | 0.000 | False | 0.180 | 0.121 | False |
| realprize | Blended | 14->30 | 0.000 | 0.000 | False | 0.000 | False | 0.236 | 0.116 | False |
| realprize | Blended | 30->60 | 0.000 | 0.000 | False | 0.000 | False | 0.147 | 0.115 | False |
| realprize | Blended | 60->90 | 0.000 | 0.000 | False | 0.000 | False | 0.123 | 0.097 | False |
| realprize | Blended | 90->120 | 0.000 | 0.000 | False | 0.000 | False | 0.229 | 0.073 | False |
| lonestar | Web | 1->7 | 0.000 | 0.010 | True | 0.096 | True | 0.534 | 0.324 | True |
| lonestar | Web | 7->14 | 0.000 | 0.010 | True | 0.118 | True | 0.285 | 0.183 | True |
| lonestar | Web | 14->30 | 0.000 | 0.010 | True | 0.088 | True | 0.417 | 0.206 | True |
| lonestar | Web | 30->60 | 0.000 | 0.010 | True | 0.098 | True | 0.421 | 0.194 | True |
| lonestar | Web | 60->90 | 0.000 | 0.005 | True | 0.082 | False | 0.204 | 0.149 | False |
| lonestar | Web | 90->120 | 0.000 | 0.000 | False | 0.000 | False | 0.186 | 0.097 | False |
| lonestar | Affiliate | 1->7 | 0.010 | 0.010 | False | 0.280 | True | 0.186 | 0.124 | False |
| lonestar | Affiliate | 7->14 | 0.010 | 0.010 | False | 0.291 | True | 0.091 | 0.091 | False |
| lonestar | Affiliate | 14->30 | 0.010 | 0.010 | False | 0.392 | True | 0.102 | 0.099 | False |
| lonestar | Affiliate | 30->60 | 0.010 | 0.010 | False | 0.329 | True | 0.105 | 0.097 | False |
| lonestar | Affiliate | 60->90 | 0.010 | 0.010 | False | 0.334 | True | 0.077 | 0.077 | False |
| lonestar | Affiliate | 90->120 | 0.010 | 0.010 | False | 0.351 | True | 0.060 | 0.060 | False |
| lonestar | Blended | 1->7 | 0.000 | 0.005 | True | 0.141 | True | 0.258 | 0.152 | True |
| lonestar | Blended | 7->14 | 0.000 | 0.000 | False | 0.000 | False | 0.133 | 0.106 | False |
| lonestar | Blended | 14->30 | 0.000 | 0.000 | False | 0.000 | False | 0.177 | 0.133 | False |
| lonestar | Blended | 30->60 | 0.000 | 0.000 | False | 0.000 | False | 0.115 | 0.095 | False |
| lonestar | Blended | 60->90 | 0.000 | 0.000 | False | 0.000 | False | 0.115 | 0.097 | False |
| lonestar | Blended | 90->120 | 0.000 | 0.000 | False | 0.000 | False | 0.054 | 0.054 | False |

## How to read this

- **Shape (primary):** did realized *pace* to day 120 match the frozen raw path?
- Same actuals as the production freeze (raw ARPU; $0 users in N).
- Adjusted sits below actual ratio by ~organic, by design. Not the verdict.

Not a methodology lock.
