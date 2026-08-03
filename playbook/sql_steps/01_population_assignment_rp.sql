-- Step 01 — RealPrize: population + first cost_date (Excel check)
-- What this proves: each user gets one population label and one cohort date
--   from analytics.realprize_cost_per_user, matching the Combined notebook mapping.
-- Cost note: narrow recent window only. Widen after you trust the mapping.

-- Knobs (edit if needed)
-- Window: last 14 days of cost_date (cheap check)

WITH mapped AS (
  SELECT
    id AS user_id,
    affid,
    channel_type,
    DATE(cost_date) AS cost_date,
    CASE
      WHEN affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069) THEN 'Web'
      WHEN affid = 1 THEN 'App'
      WHEN affid IN (64, 71) THEN 'PPC'
      WHEN affid IN (0, 78, 2290) THEN 'Organic'
      ELSE 'Affiliate'
    END AS population,
    -- Used later for organic share (App organic vs acquired)
    CASE WHEN affid = 1 THEN 'app' ELSE 'non_app' END AS scope,
    CASE
      WHEN affid = 1 AND channel_type = 'app_organic' THEN 'organic'
      WHEN affid = 1 THEN 'acquired'
      WHEN affid IN (0, 78, 2290) THEN 'organic'
      ELSE 'acquired'
    END AS bucket
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    AND affid != 4313   -- TikTok excluded in predecessor
    AND id > 0
),

-- One row per user: earliest cost_date in this window (cohort date)
-- Note: full pipeline uses MIN(cost_date) over the full SQL floor window,
-- then again MIN per (population, id). For this check we only look at 14 days.
user_cohort AS (
  SELECT
    user_id,
    population,
    scope,
    bucket,
    MIN(cost_date) AS first_cost_date,
    ANY_VALUE(affid) AS example_affid  -- one affid seen; user may have multiple rows
  FROM mapped
  GROUP BY user_id, population, scope, bucket
)

-- A) Summary counts — start here in Excel
SELECT
  population,
  scope,
  bucket,
  COUNT(*) AS n_users,
  MIN(first_cost_date) AS min_cost_date,
  MAX(first_cost_date) AS max_cost_date
FROM user_cohort
GROUP BY population, scope, bucket
ORDER BY population, scope, bucket;
