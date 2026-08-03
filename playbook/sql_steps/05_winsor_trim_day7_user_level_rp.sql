-- Step 05 — Winsor trim at day 7 (user-level Excel check)
-- Teaching cohort: App, cost_date = 2026-06-25 (~136 depositors by day 7).
--   (Web cohorts are too thin for 1% to visibly bite; Combined uses winsor 1% on Web
--    and winsor 0% on App — here we only learn the MATH on App data.)
--
-- Rule (depositors only):
--   cap = 99th percentile of raw_cum among users with raw_cum > 0
--   capped_cum = LEAST(raw_cum, cap)
--   users are NOT removed
--
-- Excel: sort by raw_cum DESC; anyone above cap should have was_capped = TRUE
--         and capped_cum = cap.

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE DATE(cost_date) = DATE('2026-06-25')
    AND affid = 1   -- App
    AND id > 0
  GROUP BY id
),

deposits AS (
  SELECT
    playerId AS user_id,
    DATE(date) AS deposit_date,
    SUM(amount) / 100.0 AS amount
  FROM `realprize.casino_astropay_dmn`
  WHERE Status = 'APPROVED'
    AND date BETWEEN DATE('2026-06-25') AND DATE('2026-07-01')  -- dsi 0..6
  GROUP BY 1, 2
),

per_user AS (
  SELECT
    u.user_id,
    u.cost_date,
    ROUND(COALESCE(SUM(d.amount), 0), 2) AS raw_cum_day7
  FROM users u
  LEFT JOIN deposits d
    ON d.user_id = u.user_id
   AND DATE_DIFF(d.deposit_date, u.cost_date, DAY) BETWEEN 0 AND 6
  GROUP BY u.user_id, u.cost_date
),

caps AS (
  SELECT
    ROUND(PERCENTILE_CONT(raw_cum_day7, 0.99) OVER (), 2) AS winsor_cap_p99
  FROM per_user
  WHERE raw_cum_day7 > 0
  LIMIT 1
)

SELECT
  p.user_id,
  p.cost_date,
  p.raw_cum_day7,
  c.winsor_cap_p99,
  ROUND(LEAST(p.raw_cum_day7, c.winsor_cap_p99), 2) AS capped_cum_day7,
  p.raw_cum_day7 > c.winsor_cap_p99 AS was_capped
FROM per_user p
CROSS JOIN caps c
ORDER BY p.raw_cum_day7 DESC, p.user_id;
