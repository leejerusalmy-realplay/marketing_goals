*Lee Jerusalmy*

# SQL steps (Excel checks) — RP + LS

One SQL file per calculation idea. Naming: `NN_short_name.sql`.

**Shared math:** same formulas for both brands (dsi rule, winsor definition, patch growth, goals).  
**Brand config differs:** tables, affid lists, winsor %, CV flags, min_cohort_dates, organic scope — see `CONFIG_AND_KNOBS.md` and `METHODOLOGY.md`.

Most early steps are **RealPrize fixtures** (cheaper first lock). To port a check to LoneStar: swap tables + affid filters + knobs (do **not** change day/dsi math).

| Step | File | Brand focus | What you check |
|------|------|-------------|----------------|
| 01 | `01_population_assignment_rp.sql` | RP (port to LS: affid map) | Population counts |
| 01b | `01b_population_sample_users_rp.sql` | RP | Sample users + scope/bucket |
| 01c | `01c_id_uniqueness_check_rp.sql` | RP | id>0 uniqueness |
| 02 | `02_dsi_cumulative_revenue_sample_rp.sql` | RP (math shared) | dsi + cum |
| 02b–02c | `02b_*` / `02c_*` | RP | Join / pre-cost deposits |
| 03 | `03_cohort_arpu_rp.sql` | RP | Cohort ARPU days 1/7/14/30 |
| 03b–03c | `03b_*` / `03c_*` | RP | User-level; dsi≤D−1 proof |
| 04 | `04_patch_growth_ratio_1_to_7_rp.sql` | RP | ARPU_7 / ARPU_1 |
| 04b | `04b_*` | RP | One date user-level |
| 05 | `05_winsor_trim_day7_user_level_rp.sql` | RP (winsor math shared) | Who gets capped |
| 05b | `05b_trim_methods_compare_summary_rp.sql` | RP lab | no_trim vs winsor vs cohort_trim |
| 06 | `06_organic_share_non_app_h30_rp.sql` | **RP** non_app | Organic @ H30 — LS would use scope=all |
| 07 | `07_goal_ratio_from_curve_toy.sql` | Brand-free | raw / adjusted goals |
| 08 | `08a`–`08d` + `08_python_parity_README.md` | **RP Web** fixture | Full patch 1→7 pre/post winsor 1% |
| 09 | `09_prev_month_best_goal_horizon.sql` | RP + LS | Prev calendar month ROAS vs adjusted goals → best H (RMSE) |
| 09a | `09a_prev_month_roas_checkpoints.sql` | RP + LS | Prev-month ROAS only (join to goals in Sheets) |

Each file: runnable alone in BigQuery → Excel → verify before next step.

### When checking LS specifically

| Change | RP → LS |
|--------|---------|
| Cost / deposit tables | lonestar.* |
| Exclude affids | 4866, 7127 |
| Web affids | LS list in `CONFIG_AND_KNOBS` / yaml |
| Web winsor | **off (0%)** — 08d style not used for LS Web |
| Organic | no scope/bucket SQL; one share for Web/Aff |
| min_cohort_dates | **20** (behavioral; rarely appears in single-date toys) |

**Step 05 / 05b:** winsor keeps users; cohort_trim removes. Production = winsor only (`TRIM_BY_POPULATION.md`).

**Step 07:** UNNEST only; brand-independent formula.

**Knobs reference:** `../CONFIG_AND_KNOBS.md`.
