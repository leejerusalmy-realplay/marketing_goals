-- Step 08d — RealPrize Web full patch 1→7: same as 08c AFTER winsor 1%
-- Fixture: cost_date = 2026-06-23, Web, PRODUCTION trim
-- Cap = p99 of depositors’ cum at day 7 within this cost_date; apply to all day cums

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

cap_tbl AS (
  SELECT APPROX_QUANTILES(c7, 100)[OFFSET(99)] AS cap_e
  FROM per_user
  WHERE c7 > 0
),

capped AS (
  SELECT
    p.user_id,
    c.cap_e,
    LEAST(p.c1, c.cap_e) AS c1,
    LEAST(p.c2, c.cap_e) AS c2,
    LEAST(p.c3, c.cap_e) AS c3,
    LEAST(p.c4, c.cap_e) AS c4,
    LEAST(p.c5, c.cap_e) AS c5,
    LEAST(p.c6, c.cap_e) AS c6,
    LEAST(p.c7, c.cap_e) AS c7,
    IF(p.c7 > c.cap_e, 1, 0) AS hit_cap
  FROM per_user p
  CROSS JOIN cap_tbl c
),

agg AS (
  SELECT
    COUNT(*) AS n_users,
    SUM(hit_cap) AS n_users_hit_cap,
    ANY_VALUE(cap_e) AS winsor_cap_usd,
    SUM(c1) AS s1, SUM(c2) AS s2, SUM(c3) AS s3, SUM(c4) AS s4,
    SUM(c5) AS s5, SUM(c6) AS s6, SUM(c7) AS s7,
    COUNTIF(c7 > 0) AS n_depositors_d7
  FROM capped
),

arpu AS (
  SELECT
    n_users,
    n_users_hit_cap,
    winsor_cap_usd,
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
  'winsor_1pct' AS trim_mode,
  n_users,
  n_depositors_d7,
  n_users_hit_cap,
  ROUND(winsor_cap_usd, 4) AS winsor_cap_usd,
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
