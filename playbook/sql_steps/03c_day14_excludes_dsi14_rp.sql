-- Step 03c — Prove day-14 ARPU excludes deposits on dsi = 14
-- Predecessor rule: ARPU at day D uses cum through dsi <= (D - 1).
--   So day 14 = dsi 0..13 only. A deposit on dsi = 14 is NOT in day-14 ARPU
--   (it first enters at day 15).
--
-- Fixed Web cohort with known dsi=14 depositors: 2026-06-17
-- (the auto-picked latest cohort in 03 had zero dsi=14 deposits)
--
-- Excel:
--   cum_through_dsi_14 = cum_through_dsi_13 + amount_on_dsi_14
--   value_used_in_day14_arpu = cum_through_dsi_13  ← dsi 14 excluded

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE DATE(cost_date) = DATE('2026-06-17')
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)
    AND affid != 4313
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
    AND date BETWEEN DATE('2026-06-17') AND DATE('2026-07-10')
  GROUP BY 1, 2
),

user_dsi AS (
  SELECT
    u.user_id,
    u.cost_date,
    d.deposit_date,
    DATE_DIFF(d.deposit_date, u.cost_date, DAY) AS dsi,
    SUM(d.amount) AS amount
  FROM users u
  INNER JOIN deposits d ON d.user_id = u.user_id
  WHERE DATE_DIFF(d.deposit_date, u.cost_date, DAY) BETWEEN 0 AND 20
  GROUP BY 1, 2, 3, 4
),

agg AS (
  SELECT
    user_id,
    cost_date,
    ROUND(SUM(IF(dsi <= 13, amount, 0)), 2) AS cum_through_dsi_13,
    ROUND(SUM(IF(dsi = 14, amount, 0)), 2) AS amount_on_dsi_14,
    ROUND(SUM(IF(dsi <= 14, amount, 0)), 2) AS cum_through_dsi_14
  FROM user_dsi
  GROUP BY user_id, cost_date
  HAVING SUM(IF(dsi = 14, amount, 0)) > 0
),

dsi14_detail AS (
  SELECT
    user_id,
    STRING_AGG(
      CONCAT(CAST(deposit_date AS STRING), ' → $', CAST(ROUND(amount, 2) AS STRING)),
      ' | '
      ORDER BY deposit_date
    ) AS deposits_on_dsi_14_detail
  FROM user_dsi
  WHERE dsi = 14
  GROUP BY user_id
)

SELECT
  a.cost_date AS cohort_cost_date,
  a.user_id,
  a.cum_through_dsi_13,
  a.amount_on_dsi_14,
  a.cum_through_dsi_14,
  d.deposits_on_dsi_14_detail,
  a.cum_through_dsi_13 AS value_used_in_day14_arpu,
  a.amount_on_dsi_14 AS value_excluded_from_day14_arpu
FROM agg a
LEFT JOIN dsi14_detail d USING (user_id)
ORDER BY a.amount_on_dsi_14 DESC, a.user_id;
