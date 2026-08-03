-- Step 04b — One cohort date: user-level for Excel recompute of growth ratio
-- Pick the latest Web cost_date in the 04 window with ARPU_s > 0.
-- Excel:
--   arpu_s = AVERAGE(cum_s)  or SUM(cum_s)/COUNT
--   arpu_e = SUM(cum_e)/COUNT
--   growth = arpu_e / arpu_s

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 50 DAY)
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)
    AND id > 0
  GROUP BY id
),

cohort_users_all AS (
  SELECT user_id, cost_date
  FROM users
  WHERE cost_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 41 DAY)
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
  FROM cohort_users_all c
  INNER JOIN deposits d ON d.user_id = c.user_id
  WHERE DATE_DIFF(d.deposit_date, c.cost_date, DAY) BETWEEN 0 AND 6
  GROUP BY 1, 2, 3
),

per_user_all AS (
  SELECT
    c.user_id,
    c.cost_date,
    COALESCE(SUM(IF(ud.dsi <= 0, ud.amount, 0)), 0) AS cum_s,
    COALESCE(SUM(IF(ud.dsi <= 6, ud.amount, 0)), 0) AS cum_e
  FROM cohort_users_all c
  LEFT JOIN user_dsi ud
    ON ud.user_id = c.user_id AND ud.cost_date = c.cost_date
  GROUP BY c.user_id, c.cost_date
),

pick AS (
  SELECT cost_date
  FROM per_user_all
  GROUP BY cost_date
  HAVING SUM(cum_s) > 0
  ORDER BY cost_date DESC
  LIMIT 1
)

SELECT
  p.user_id,
  p.cost_date,
  ROUND(p.cum_s, 2) AS cum_through_day1_dsi0,
  ROUND(p.cum_e, 2) AS cum_through_day7_dsi0_to_6
FROM per_user_all p
INNER JOIN pick USING (cost_date)
ORDER BY p.cum_e DESC, p.user_id;
