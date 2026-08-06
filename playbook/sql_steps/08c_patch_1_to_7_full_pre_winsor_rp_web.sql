-- Step 08c — RealPrize Web full patch 1→7: ARPU each day + day-steps + patch growth
-- Fixture: cost_date = 2026-06-23, Web, PRE-WINSOR
--
-- Day D: dsi ≤ D-1 | growth_step_k = ARPU_k/ARPU_{k-1} | patch growth = ARPU_7/ARPU_1
-- Must match SUM of 08b columns / n_users.

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
    AND date BETWEEN DATE '2026-06-23' AND DATE '2026-06-29'
  GROUP BY 1, 2
),

user_dsi AS (
  SELECT
    c.user_id,
    DATE_DIFF(d.deposit_date, c.cost_date, DAY) AS dsi,
    SUM(d.amount_usd) AS amount_usd
  FROM cohort c
  INNER JOIN deposits d ON d.user_id = c.user_id
  WHERE DATE_DIFF(d.deposit_date, c.cost_date, DAY) BETWEEN 0 AND 6
  GROUP BY 1, 2
),

per_user AS (
  SELECT
    c.user_id,
    COALESCE(SUM(IF(u.dsi <= 0, u.amount_usd, 0)), 0) AS c1,
    COALESCE(SUM(IF(u.dsi <= 1, u.amount_usd, 0)), 0) AS c2,
    COALESCE(SUM(IF(u.dsi <= 2, u.amount_usd, 0)), 0) AS c3,
    COALESCE(SUM(IF(u.dsi <= 3, u.amount_usd, 0)), 0) AS c4,
    COALESCE(SUM(IF(u.dsi <= 4, u.amount_usd, 0)), 0) AS c5,
    COALESCE(SUM(IF(u.dsi <= 5, u.amount_usd, 0)), 0) AS c6,
    COALESCE(SUM(IF(u.dsi <= 6, u.amount_usd, 0)), 0) AS c7
  FROM cohort c
  LEFT JOIN user_dsi u ON u.user_id = c.user_id
  GROUP BY c.user_id
),

agg AS (
  SELECT
    COUNT(*) AS n_users,
    SUM(c1) AS s1, SUM(c2) AS s2, SUM(c3) AS s3, SUM(c4) AS s4,
    SUM(c5) AS s5, SUM(c6) AS s6, SUM(c7) AS s7,
    COUNTIF(c7 > 0) AS n_depositors_d7
  FROM per_user
),

arpu AS (
  SELECT
    n_users,
    n_depositors_d7,
    s1 / n_users AS a1,
    s2 / n_users AS a2,
    s3 / n_users AS a3,
    s4 / n_users AS a4,
    s5 / n_users AS a5,
    s6 / n_users AS a6,
    s7 / n_users AS a7,
    s1, s2, s3, s4, s5, s6, s7
  FROM agg
)

SELECT
  DATE '2026-06-23' AS cohort_cost_date,
  'Web' AS population,
  '1->7' AS patch,
  'pre_winsor' AS trim_mode,
  n_users,
  n_depositors_d7,
  ROUND(s1, 4) AS sum_day1,
  ROUND(s2, 4) AS sum_day2,
  ROUND(s3, 4) AS sum_day3,
  ROUND(s4, 4) AS sum_day4,
  ROUND(s5, 4) AS sum_day5,
  ROUND(s6, 4) AS sum_day6,
  ROUND(s7, 4) AS sum_day7,
  ROUND(a1, 6) AS arpu_day1,
  ROUND(a2, 6) AS arpu_day2,
  ROUND(a3, 6) AS arpu_day3,
  ROUND(a4, 6) AS arpu_day4,
  ROUND(a5, 6) AS arpu_day5,
  ROUND(a6, 6) AS arpu_day6,
  ROUND(a7, 6) AS arpu_day7,
  ROUND(SAFE_DIVIDE(a2, a1), 6) AS growth_step_2,
  ROUND(SAFE_DIVIDE(a3, a2), 6) AS growth_step_3,
  ROUND(SAFE_DIVIDE(a4, a3), 6) AS growth_step_4,
  ROUND(SAFE_DIVIDE(a5, a4), 6) AS growth_step_5,
  ROUND(SAFE_DIVIDE(a6, a5), 6) AS growth_step_6,
  ROUND(SAFE_DIVIDE(a7, a6), 6) AS growth_step_7,
  ROUND(SAFE_DIVIDE(a7, a1), 6) AS growth_ratio_patch_1_to_7
FROM arpu;
