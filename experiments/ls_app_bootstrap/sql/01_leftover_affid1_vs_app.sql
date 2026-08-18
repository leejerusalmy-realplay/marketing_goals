-- LS App leftover affid=1 vs real App (launch 2026-07-16)
-- Cheap: cost table for counts; deposits only for the Combined 1→7 D1 window.
-- Excel check: leftover users are few overall, but they dominate long patches
-- and inflate D1. Not a methodology lock.

-- 1) Volume by era
WITH users AS (
  SELECT
    id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.lonestar_cost_per_user`
  WHERE cost_date >= DATE '2025-06-01'
    AND affid = 1
    AND id > 0
    AND affid NOT IN (4866, 7127)
  GROUP BY id
)
SELECT
  CASE WHEN cost_date < DATE '2026-07-16' THEN 'pre_launch' ELSE 'post_launch' END AS era,
  COUNT(*) AS n_users,
  COUNT(DISTINCT cost_date) AS n_dates,
  MIN(cost_date) AS min_cost_date,
  MAX(cost_date) AS max_cost_date
FROM users
GROUP BY 1
ORDER BY 1;


-- 2) Combined patch windows: all dates vs launch-floor dates
-- Window = [as_of - (e + 34), as_of - e]. Floor = cost_date >= 2026-07-16.
-- Run this as a second query in BQ / Excel.
WITH users AS (
  SELECT
    id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.lonestar_cost_per_user`
  WHERE cost_date >= DATE '2026-05-01'
    AND affid = 1
    AND id > 0
    AND affid NOT IN (4866, 7127)
  GROUP BY id
),
windows AS (
  SELECT * FROM UNNEST([
    STRUCT('asof_0803_e7'  AS win, DATE '2026-06-23' AS cohort_start, DATE '2026-07-27' AS cohort_end),
    STRUCT('asof_0803_e14',        DATE '2026-06-16',                 DATE '2026-07-20'),
    STRUCT('asof_0803_e30',        DATE '2026-05-31',                 DATE '2026-07-04'),
    STRUCT('asof_0816_e7',         DATE '2026-07-06',                 DATE '2026-08-09'),
    STRUCT('asof_0816_e14',        DATE '2026-06-29',                 DATE '2026-08-02'),
    STRUCT('asof_0816_e30',        DATE '2026-06-13',                 DATE '2026-07-17'),
    STRUCT('asof_0817_e30',        DATE '2026-06-14',                 DATE '2026-07-18')
  ])
)
SELECT
  w.win,
  COUNTIF(u.cost_date BETWEEN w.cohort_start AND w.cohort_end) AS n_users_all,
  COUNT(DISTINCT IF(u.cost_date BETWEEN w.cohort_start AND w.cohort_end, u.cost_date, NULL)) AS n_dates_all,
  COUNTIF(u.cost_date BETWEEN w.cohort_start AND w.cohort_end AND u.cost_date < DATE '2026-07-16') AS n_users_pre,
  COUNT(DISTINCT IF(
    u.cost_date BETWEEN w.cohort_start AND w.cohort_end AND u.cost_date < DATE '2026-07-16',
    u.cost_date, NULL
  )) AS n_dates_pre,
  COUNTIF(u.cost_date BETWEEN GREATEST(w.cohort_start, DATE '2026-07-16') AND w.cohort_end) AS n_users_launch_floor,
  COUNT(DISTINCT IF(
    u.cost_date BETWEEN GREATEST(w.cohort_start, DATE '2026-07-16') AND w.cohort_end,
    u.cost_date, NULL
  )) AS n_dates_launch_floor
FROM windows w
CROSS JOIN users u
GROUP BY w.win
ORDER BY w.win;


-- 3) Raw D1 ARPU in the Combined as_of 2026-08-03 patch 1→7 window
-- (Jun 23–Jul 27). Combined D1 is after growth/CV; this is the raw first-day $.
WITH users AS (
  SELECT
    id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.lonestar_cost_per_user`
  WHERE cost_date >= DATE '2026-06-01'
    AND affid = 1
    AND id > 0
    AND affid NOT IN (4866, 7127)
  GROUP BY id
),
cohort AS (
  SELECT
    id,
    cost_date,
    CASE WHEN cost_date < DATE '2026-07-16' THEN 'pre_launch' ELSE 'post_launch' END AS era
  FROM users
  WHERE cost_date BETWEEN DATE '2026-06-23' AND DATE '2026-07-27'
),
d1 AS (
  SELECT
    c.era,
    COUNT(*) AS n_users,
    SUM(IFNULL(d.amount, 0)) / 100.0 AS d1_dollars
  FROM cohort c
  LEFT JOIN (
    SELECT playerId AS id, DATE(date) AS deposit_date, SUM(amount) AS amount
    FROM `lonestar.casino_astropay_dmn`
    WHERE Status = 'APPROVED'
      AND date BETWEEN DATE '2026-06-23' AND DATE '2026-07-27'
    GROUP BY 1, 2
  ) d
    ON d.id = c.id AND d.deposit_date = c.cost_date
  GROUP BY c.era
)
SELECT
  era,
  n_users,
  ROUND(d1_dollars, 2) AS d1_dollars,
  ROUND(d1_dollars / n_users, 4) AS d1_arpu
FROM d1
UNION ALL
SELECT
  'all_in_window',
  SUM(n_users),
  ROUND(SUM(d1_dollars), 2),
  ROUND(SUM(d1_dollars) / SUM(n_users), 4)
FROM d1
ORDER BY era;
