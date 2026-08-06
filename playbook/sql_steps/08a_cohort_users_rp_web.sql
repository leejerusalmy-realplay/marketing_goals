-- Step 08a — RealPrize Web: who is in ONE cohort (cost_date)
-- Fixture: RealPrize / Web / cost_date = 2026-06-23 / patch 1→7
--
-- What to check:
--   n_users = N used in all denominators below
--   Spot-check ids: Web affid, id > 0, MIN(cost_date) = 2026-06-23

WITH user_min_cost AS (
  -- One row per user (after Web / id filters); cost_date = earliest cost day
  SELECT
    id AS user_id,
    MIN(DATE(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date BETWEEN DATE '2026-06-14' AND DATE '2026-07-03'
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)  -- Web
    AND affid != 4313
    AND id > 0
  GROUP BY id
),

cohort AS (
  SELECT user_id, cost_date
  FROM user_min_cost
  WHERE cost_date = DATE '2026-06-23'
)

SELECT
  DATE '2026-06-23' AS cohort_cost_date,
  'Web' AS population,
  '1->7' AS patch,
  COUNT(*) AS n_users
FROM cohort;

-- Sample (optional):
-- SELECT user_id, cost_date FROM cohort ORDER BY user_id LIMIT 50;
