-- Step 04 — RealPrize: patch growth ratio (ARPU_e / ARPU_s)
-- What this proves:
--   For patch (s, e) = (1, 7):
--     ARPU_s = cum through dsi <= s-1 = dsi 0
--     ARPU_e = cum through dsi <= e-1 = dsi 0..6
--     growth_ratio = ARPU_e / ARPU_s
--   One row per cohort cost_date (Web). Non-depositors still in denominator.
--
-- Cheap: Web, last ~35 mature cohort dates (cost_date <= today-7), patch 1→7 only.

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 50 DAY)
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)  -- Web
    AND id > 0
  GROUP BY id
),

-- Cohorts old enough that day-7 ARPU is fully observed
cohort_users AS (
  SELECT user_id, cost_date
  FROM users
  WHERE cost_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 41 DAY)  -- ~35 days of cohorts
),

deposits AS (
  SELECT
    playerId AS user_id,
    DATE(date) AS deposit_date,
    SUM(amount) / 100.0 AS amount
  FROM `realprize.casino_astropay_dmn`
  WHERE Status = 'APPROVED'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 50 DAY)
  GROUP BY 1, 2
),

user_dsi AS (
  SELECT
    c.user_id,
    c.cost_date,
    DATE_DIFF(d.deposit_date, c.cost_date, DAY) AS dsi,
    SUM(d.amount) AS amount
  FROM cohort_users c
  INNER JOIN deposits d ON d.user_id = c.user_id
  WHERE DATE_DIFF(d.deposit_date, c.cost_date, DAY) BETWEEN 0 AND 6
  GROUP BY 1, 2, 3
),

per_user AS (
  SELECT
    c.user_id,
    c.cost_date,
    COALESCE(SUM(IF(ud.dsi <= 0, ud.amount, 0)), 0) AS cum_s,  -- through day 1 (dsi 0)
    COALESCE(SUM(IF(ud.dsi <= 6, ud.amount, 0)), 0) AS cum_e   -- through day 7 (dsi 0..6)
  FROM cohort_users c
  LEFT JOIN user_dsi ud
    ON ud.user_id = c.user_id AND ud.cost_date = c.cost_date
  GROUP BY c.user_id, c.cost_date
)

SELECT
  cost_date,
  COUNT(*) AS n_users,
  ROUND(SUM(cum_s), 2) AS sum_cum_s,
  ROUND(SUM(cum_e), 2) AS sum_cum_e,
  ROUND(SUM(cum_s) / COUNT(*), 4) AS arpu_s,   -- ARPU day 1
  ROUND(SUM(cum_e) / COUNT(*), 4) AS arpu_e,   -- ARPU day 7
  ROUND(
    SAFE_DIVIDE(SUM(cum_e) / COUNT(*), SUM(cum_s) / COUNT(*)),
    4
  ) AS growth_ratio_1_to_7
FROM per_user
GROUP BY cost_date
HAVING SUM(cum_s) > 0   -- need ARPU_s > 0 for a defined ratio (same spirit as notebook)
ORDER BY cost_date;
