-- =============================================================================
-- Previous-month ROAS checkpoints only (no goals embedded)
-- Single-statement (Simba JDBC friendly). Join to goals in Sheets/Colab.
-- =============================================================================
-- Edit dates in params CTE if needed.
-- =============================================================================

WITH params AS (
  SELECT
    DATE '2026-08-05' AS goals_run_date,
    DATE '2026-08-05' AS as_of_date,
    DATE_TRUNC(DATE_SUB(DATE '2026-08-05', INTERVAL 1 MONTH), MONTH) AS prev_month_start,
    LAST_DAY(DATE_SUB(DATE '2026-08-05', INTERVAL 1 MONTH), MONTH) AS prev_month_end
),
base AS (
  SELECT
    CASE brand WHEN 'RealPrize' THEN 'realprize' WHEN 'LoneStar' THEN 'lonestar' ELSE LOWER(brand) END AS brand,
    CASE marketing_population
      WHEN 'WEB' THEN 'Web' WHEN 'APP' THEN 'App' WHEN 'Affiliate' THEN 'Affiliate'
      ELSE marketing_population END AS population,
    DATE(cost_date) AS cost_date,
    SUM(cost) AS cost,
    SUM(LTV_D1) AS ltv_1, SUM(LTV_D2) AS ltv_2, SUM(LTV_D3) AS ltv_3,
    SUM(LTV_D4) AS ltv_4, SUM(LTV_D5) AS ltv_5, SUM(LTV_D6) AS ltv_6,
    SUM(LTV_D7) AS ltv_7, SUM(LTV_D14) AS ltv_14, SUM(LTV_D30) AS ltv_30
  FROM `oceanic-citadel-454608-d2.ETL.Real_Play_Marketing_Cohort`
  CROSS JOIN params p
  WHERE brand IN ('RealPrize', 'LoneStar')
    AND marketing_population IN ('WEB', 'APP', 'Affiliate')
    AND DATE(cost_date) BETWEEN p.prev_month_start AND p.prev_month_end
  GROUP BY 1, 2, 3
),
all_pops AS (
  SELECT * FROM base
  UNION ALL
  SELECT brand, 'Blended' AS population, cost_date,
         SUM(cost), SUM(ltv_1), SUM(ltv_2), SUM(ltv_3), SUM(ltv_4), SUM(ltv_5),
         SUM(ltv_6), SUM(ltv_7), SUM(ltv_14), SUM(ltv_30)
  FROM base
  GROUP BY 1, 2, 3
),
unpivoted AS (
  SELECT
    a.brand, a.population, a.cost_date, a.cost, u.day, u.ltv,
    DATE_DIFF(p.as_of_date, a.cost_date, DAY) AS age_days
  FROM all_pops a
  CROSS JOIN params p
  CROSS JOIN UNNEST([
    STRUCT(1 AS day, a.ltv_1 AS ltv), STRUCT(2 AS day, a.ltv_2 AS ltv),
    STRUCT(3 AS day, a.ltv_3 AS ltv), STRUCT(4 AS day, a.ltv_4 AS ltv),
    STRUCT(5 AS day, a.ltv_5 AS ltv), STRUCT(6 AS day, a.ltv_6 AS ltv),
    STRUCT(7 AS day, a.ltv_7 AS ltv), STRUCT(14 AS day, a.ltv_14 AS ltv),
    STRUCT(30 AS day, a.ltv_30 AS ltv)
  ]) AS u
)
SELECT
  p.goals_run_date,
  p.prev_month_start,
  p.prev_month_end,
  'd7_pool' AS pool,
  u.brand,
  u.population,
  u.day,
  SAFE_DIVIDE(SUM(u.ltv), SUM(u.cost)) AS month_roas,
  SUM(u.cost) AS cost,
  COUNT(DISTINCT u.cost_date) AS n_days
FROM unpivoted u
CROSS JOIN params p
WHERE u.age_days >= 7 AND u.day <= 7
GROUP BY 1, 2, 3, 4, 5, 6, 7

UNION ALL

SELECT
  p.goals_run_date,
  p.prev_month_start,
  p.prev_month_end,
  'd30_pool' AS pool,
  u.brand,
  u.population,
  u.day,
  SAFE_DIVIDE(SUM(u.ltv), SUM(u.cost)) AS month_roas,
  SUM(u.cost) AS cost,
  COUNT(DISTINCT u.cost_date) AS n_days
FROM unpivoted u
CROSS JOIN params p
WHERE u.age_days >= 30 AND u.day <= 30
GROUP BY 1, 2, 3, 4, 5, 6, 7

ORDER BY pool, brand, population, day;
