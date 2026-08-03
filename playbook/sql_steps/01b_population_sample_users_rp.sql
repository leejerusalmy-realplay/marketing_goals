-- Step 01b — RealPrize: sample users for Excel (after 01 summary looks sane)
-- What this proves: you can spot-check affid → population by hand.
-- Export to Excel and verify a few Web / App / PPC / Organic / Affiliate rows.

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
    CASE WHEN affid = 1 THEN 'app' ELSE 'non_app' END AS scope,
    CASE
      WHEN affid = 1 AND channel_type = 'app_organic' THEN 'organic'
      WHEN affid = 1 THEN 'acquired'
      WHEN affid IN (0, 78, 2290) THEN 'organic'
      ELSE 'acquired'
    END AS bucket
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    AND affid != 4313
    AND id > 0
),

user_cohort AS (
  SELECT
    user_id,
    population,
    scope,
    bucket,
    MIN(cost_date) AS first_cost_date,
    ARRAY_AGG(DISTINCT affid ORDER BY affid LIMIT 5) AS affids_seen
  FROM mapped
  GROUP BY user_id, population, scope, bucket
),

ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY population ORDER BY first_cost_date DESC) AS rn
  FROM user_cohort
)

-- Up to 20 users per population — small Excel sheet
SELECT
  user_id,
  population,
  scope,
  bucket,
  first_cost_date,
  affids_seen
FROM ranked
WHERE rn <= 20
ORDER BY population, first_cost_date DESC;
