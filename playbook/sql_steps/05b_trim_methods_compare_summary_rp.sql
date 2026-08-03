-- Step 05b — Summary: no_trim vs winsor 1% vs cohort_trim 1%
-- Same App cohort 2026-06-25, ARPU day 7 (dsi 0..6).
--
-- winsor: keep ALL users; cap revenue at p99 of depositors
-- cohort_trim: REMOVE users with cum > p99 (top 1% of depositors); keep rest
--
-- Excel: recompute from 05 user-level export.

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE DATE(cost_date) = DATE('2026-06-25')
    AND affid = 1
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
    AND date BETWEEN DATE('2026-06-25') AND DATE('2026-07-01')
  GROUP BY 1, 2
),

per_user AS (
  SELECT
    u.user_id,
    ROUND(COALESCE(SUM(d.amount), 0), 2) AS raw_cum
  FROM users u
  LEFT JOIN deposits d
    ON d.user_id = u.user_id
   AND DATE_DIFF(d.deposit_date, u.cost_date, DAY) BETWEEN 0 AND 6
  GROUP BY u.user_id, u.cost_date
),

stats AS (
  SELECT ROUND(PERCENTILE_CONT(raw_cum, 0.99) OVER (), 2) AS p99_cap
  FROM per_user
  WHERE raw_cum > 0
  LIMIT 1
),

marked AS (
  SELECT
    p.*,
    s.p99_cap,
    LEAST(p.raw_cum, s.p99_cap) AS winsor_cum,
    CASE
      WHEN p.raw_cum > 0 AND p.raw_cum > s.p99_cap THEN TRUE
      ELSE FALSE
    END AS dropped_by_cohort_trim
  FROM per_user p
  CROSS JOIN stats s
)

SELECT 'no_trim' AS method,
  COUNT(*) AS n_users,
  COUNTIF(raw_cum > 0) AS n_depositors,
  ROUND(SUM(raw_cum), 2) AS sum_cum,
  ROUND(SUM(raw_cum) / COUNT(*), 4) AS arpu_day7,
  NULL AS n_capped_or_dropped
FROM marked

UNION ALL

SELECT 'winsor_1pct',
  COUNT(*),
  COUNTIF(winsor_cum > 0),
  ROUND(SUM(winsor_cum), 2),
  ROUND(SUM(winsor_cum) / COUNT(*), 4),
  COUNTIF(raw_cum > p99_cap)
FROM marked

UNION ALL

SELECT 'cohort_trim_1pct',
  COUNTIF(NOT dropped_by_cohort_trim),
  COUNTIF(NOT dropped_by_cohort_trim AND raw_cum > 0),
  ROUND(SUM(IF(NOT dropped_by_cohort_trim, raw_cum, 0)), 2),
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(NOT dropped_by_cohort_trim, raw_cum, 0)),
      COUNTIF(NOT dropped_by_cohort_trim)
    ),
    4
  ),
  COUNTIF(dropped_by_cohort_trim)
FROM marked

ORDER BY method;
