-- RP only: how many users move if channel_type = app_affiliate → Affiliate
-- Compare v3 Goals label vs this experiment. Last 14 days. Cheap Excel check.
-- TikTok WEB 4313 excluded. Same exceptions as Combined (SEO / Shared Link / 2290).

WITH base AS (
  SELECT
    id,
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
    id,
    channel_type,
    marketing_population,
    CASE
      WHEN affid = 2290 THEN 'Organic'
      WHEN marketing_population IN ('SEO', 'Shared Link', 'Organic') THEN 'Organic'
      WHEN marketing_population = 'WEB' THEN 'Web'
      WHEN marketing_population = 'APP' THEN 'App'
      WHEN marketing_population IN ('Google PPC', 'Bing PPC', 'PPC') THEN 'PPC'
      ELSE 'Affiliate'
    END AS population_v3,
    CASE
      WHEN affid = 2290 THEN 'Organic'
      WHEN marketing_population IN ('SEO', 'Shared Link', 'Organic') THEN 'Organic'
      WHEN marketing_population = 'WEB' THEN 'Web'
      WHEN channel_type = 'app_affiliate' THEN 'Affiliate'
      WHEN marketing_population = 'APP' THEN 'App'
      WHEN marketing_population IN ('Google PPC', 'Bing PPC', 'PPC') THEN 'PPC'
      ELSE 'Affiliate'
    END AS population_experiment
  FROM base
)

-- A) Counts by v3 vs experiment label
SELECT
  population_v3,
  population_experiment,
  COUNT(*) AS n_users
FROM mapped
GROUP BY 1, 2
ORDER BY n_users DESC;


-- B) Who actually moves (should be App → Affiliate, channel_type = app_affiliate)
-- Run as a second query in BQ / Excel.
-- WITH base AS ( ... same as above ... ), mapped AS ( ... )
-- SELECT channel_type, marketing_population, COUNT(*) AS n_users
-- FROM mapped
-- WHERE population_v3 != population_experiment
-- GROUP BY 1, 2
-- ORDER BY n_users DESC;
