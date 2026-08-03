-- Step 01c — RealPrize: do positive ids ever have multiple affids / cost_dates?
-- What this proves: for id > 0 (the pipeline population), one id = one affid = one cost_date
--   in the check window. Multi cost_date rows (if any) sit on id < 0, which we exclude.
-- Cost: 14-day window.

WITH base AS (
  SELECT
    id,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT affid) AS n_affids,
    COUNT(DISTINCT DATE(cost_date)) AS n_cost_dates
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    AND affid != 4313
  GROUP BY id
)
SELECT
  CASE
    WHEN id < 0 THEN 'id_lt_0'
    WHEN id = 0 THEN 'id_eq_0'
    ELSE 'id_gt_0'
  END AS id_bucket,
  COUNT(*) AS n_users,
  COUNTIF(n_affids > 1) AS users_multi_affid,
  COUNTIF(n_cost_dates > 1) AS users_multi_cost_date,
  COUNTIF(n_rows > 1) AS users_multi_row,
  MAX(n_affids) AS max_affids,
  MAX(n_cost_dates) AS max_cost_dates
FROM base
GROUP BY 1
ORDER BY 1;
