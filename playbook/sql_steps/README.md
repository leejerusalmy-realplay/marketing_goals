# SQL steps (Excel checks)

One file per calculation. Naming: `NN_short_name.sql`.

| Step | File | What you check |
|------|------|----------------|
| 01 | `01_population_assignment_rp.sql` | Population counts (14-day window) |
| 01b | `01b_population_sample_users_rp.sql` | Spot-check users by affid → population |
| 01c | `01c_id_uniqueness_check_rp.sql` | Multi affid/cost_date only on id &lt; 0 |
| 02 | `02_dsi_cumulative_revenue_sample_rp.sql` | Per-user dsi + cum_amount (sample) |
| 02b | `02b_dsi_join_sanity_rp.sql` | Aggregate join / dsi sanity |
| 02c | `02c_deposits_before_cost_date_rp.sql` | Are deposits before cost_date possible? |
| 03 | `03_cohort_arpu_rp.sql` | Cohort ARPU at days 1/7/14/30 |
| 03b | `03b_cohort_arpu_user_level_rp.sql` | User-level rows to recompute ARPU in Excel |
| 03c | `03c_day14_excludes_dsi14_rp.sql` | Prove day 14 uses dsi≤13 only |
| 04 | `04_patch_growth_ratio_1_to_7_rp.sql` | Growth ratio ARPU_7 / ARPU_1 by cohort date |
| 04b | `04b_patch_growth_user_level_rp.sql` | User-level for one date to recompute growth |
| 05 | `05_winsor_trim_day7_user_level_rp.sql` | Winsor 1%: who gets capped (App demo cohort) |
| 05b | `05b_trim_methods_compare_summary_rp.sql` | no_trim vs winsor vs cohort_trim ARPU |
| 06 | `06_organic_share_non_app_h30_rp.sql` | Organic share at horizon 30 (non_app endpoint) |

Each file: runnable alone in BigQuery → export to Excel → verify before next step.
