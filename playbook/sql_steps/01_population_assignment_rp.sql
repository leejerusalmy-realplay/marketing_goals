-- Step 01 — RealPrize: population + first cost_date (Excel check)
-- What this proves: each user gets one population label and one cohort date
--   from analytics.realprize_cost_per_user, matching Combined v4 (2026-08-24).
-- Population from marketing_population (stg_channel_affid_mapping).
-- Exceptions: SEO / Shared Link → Organic; affid 2290 → Organic.
-- v4: channel_type = app_affiliate → Affiliate (non_app / acquired).
-- Cost note: narrow recent window only. Widen after you trust the mapping.

-- Knobs (edit if needed)
-- Window: last 14 days of cost_date (cheap check)

WITH base AS (
  SELECT
    id AS user_id,
    affid,
    channel_type,
    marketing_population,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    AND affid != 4313   -- TikTok WEB excluded
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
