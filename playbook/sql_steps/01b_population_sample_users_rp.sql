-- Step 01b — RealPrize: sample users for Excel (after 01 summary looks sane)
-- What this proves: you can spot-check marketing_population → Goals population by hand.
-- Export to Excel and verify a few Web / App / PPC / Organic / Affiliate rows.

WITH base AS (
  SELECT
    id AS user_id,
    affid,
    channel_type,
    marketing_population,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    AND affid != 4313
    AND id > 0
  GROUP BY id, affid, channel_type, marketing_population
),

mapped AS (
  SELECT
    user_id,
    affid,
    cost_date,
    CASE
      WHEN affid = 2290 THEN 'Organic'
      WHEN marketing_population IN ('SEO', 'Shared Link', 'Organic') THEN 'Organic'
      WHEN marketing_population = 'WEB' THEN 'Web'
      WHEN channel_type = 'app_affiliate' THEN 'Affiliate'
      WHEN marketing_population = 'APP' THEN 'App'
      WHEN marketing_population IN ('Google PPC', 'Bing PPC', 'PPC') THEN 'PPC'
      ELSE 'Affiliate'
    END AS population,
    CASE
      WHEN channel_type = 'app_affiliate' THEN 'non_app'
      WHEN marketing_population = 'APP' THEN 'app'
      ELSE 'non_app'
    END AS scope,
    CASE
      WHEN channel_type = 'app_affiliate' THEN 'acquired'
      WHEN marketing_population = 'APP' AND channel_type = 'app_organic' THEN 'organic'
      WHEN marketing_population = 'APP' THEN 'acquired'
      WHEN affid = 2290 THEN 'organic'
      WHEN marketing_population IN ('SEO', 'Shared Link', 'Organic') THEN 'organic'
      ELSE 'acquired'
    END AS bucket
  FROM base
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
