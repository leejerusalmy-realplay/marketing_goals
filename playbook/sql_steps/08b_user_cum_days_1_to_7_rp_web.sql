-- Step 08b — RealPrize Web full patch: per-user cum for life days 1…7
-- Fixture: cost_date = 2026-06-23, Web, patch 1→7
--
-- Day D uses dsi ≤ D-1  (Combined / Colab)
--   day 1 → dsi ≤ 0
--   …
--   day 7 → dsi ≤ 6
--
-- Export ALL rows to Excel. Then:
--   n            = COUNT(user_id)
--   sum_day_D    = SUM(cum_day_D)
--   ARPU_D       = sum_day_D / n

WITH user_min_cost AS (
  SELECT
    id AS user_id,
    MIN(DATE(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date BETWEEN DATE '2026-06-14' AND DATE '2026-07-03'
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)
    AND affid != 4313
    AND id > 0
  GROUP BY id
),

cohort AS (
  SELECT user_id, cost_date
  FROM user_min_cost
  WHERE cost_date = DATE '2026-06-23'
),

deposits AS (
  SELECT
    playerId AS user_id,
    DATE(date) AS deposit_date,
    SUM(amount) / 100.0 AS amount_usd
  FROM `realprize.casino_astropay_dmn`
  WHERE Status = 'APPROVED'
    AND date BETWEEN DATE '2026-06-23' AND DATE '2026-06-29'  -- +0..+6 days
  GROUP BY 1, 2
),

user_dsi AS (
  SELECT
    c.user_id,
    c.cost_date,
    DATE_DIFF(d.deposit_date, c.cost_date, DAY) AS dsi,
    SUM(d.amount_usd) AS amount_usd
  FROM cohort c
  INNER JOIN deposits d ON d.user_id = c.user_id
  WHERE DATE_DIFF(d.deposit_date, c.cost_date, DAY) BETWEEN 0 AND 6
  GROUP BY 1, 2, 3
)

SELECT
  c.user_id,
  c.cost_date,
  ROUND(COALESCE(SUM(IF(u.dsi <= 0, u.amount_usd, 0)), 0), 4) AS cum_day1,
  ROUND(COALESCE(SUM(IF(u.dsi <= 1, u.amount_usd, 0)), 0), 4) AS cum_day2,
  ROUND(COALESCE(SUM(IF(u.dsi <= 2, u.amount_usd, 0)), 0), 4) AS cum_day3,
  ROUND(COALESCE(SUM(IF(u.dsi <= 3, u.amount_usd, 0)), 0), 4) AS cum_day4,
  ROUND(COALESCE(SUM(IF(u.dsi <= 4, u.amount_usd, 0)), 0), 4) AS cum_day5,
  ROUND(COALESCE(SUM(IF(u.dsi <= 5, u.amount_usd, 0)), 0), 4) AS cum_day6,
  ROUND(COALESCE(SUM(IF(u.dsi <= 6, u.amount_usd, 0)), 0), 4) AS cum_day7,
  IF(COALESCE(SUM(IF(u.dsi <= 6, u.amount_usd, 0)), 0) > 0, 1, 0) AS is_depositor_by_d7
FROM cohort c
LEFT JOIN user_dsi u
  ON u.user_id = c.user_id AND u.cost_date = c.cost_date
GROUP BY c.user_id, c.cost_date
ORDER BY cum_day7 DESC, c.user_id;
