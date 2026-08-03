-- Step 03 — RealPrize: cohort ARPU at selected days (Excel check)
-- What this proves:
--   ARPU_day = (sum of each user's cumulative deposits through that day) / (all users in the cohort)
--   Non-depositors count in the denominator with cum = 0.
--   Day D uses deposits with dsi in [0, D-1]  (same as predecessor: idx = day - 1).
--
-- Cheap scope: Web only, one recent cost_date with enough users, days 1/7/14/30.

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)  -- Web
    AND affid != 4313
    AND id > 0
  GROUP BY id
),

-- Pick one cohort date: the most recent Web cost_date that is at least 30 days old
-- (so day-30 ARPU is fully observable)
cohort_pick AS (
  SELECT cost_date
  FROM users
  WHERE cost_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY cost_date
  HAVING COUNT(*) >= 20
  ORDER BY cost_date DESC
  LIMIT 1
),

cohort_users AS (
  SELECT u.user_id, u.cost_date
  FROM users u
  INNER JOIN cohort_pick p USING (cost_date)
),

deposits AS (
  SELECT
    playerId AS user_id,
    DATE(date) AS deposit_date,
    SUM(amount) / 100.0 AS amount
  FROM `realprize.casino_astropay_dmn`
  WHERE Status = 'APPROVED'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
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
  WHERE DATE_DIFF(d.deposit_date, c.cost_date, DAY) BETWEEN 0 AND 29
  GROUP BY 1, 2, 3
),

-- Cumulative through each dsi for depositors
user_cum AS (
  SELECT
    user_id,
    cost_date,
    dsi,
    SUM(amount) OVER (
      PARTITION BY user_id
      ORDER BY dsi
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cum_amount
  FROM user_dsi
),

-- For each goal day D in (1,7,14,30), cum through dsi <= D-1
days AS (
  SELECT day FROM UNNEST([1, 7, 14, 30]) AS day
),

per_user_at_day AS (
  SELECT
    c.user_id,
    c.cost_date,
    d.day,
    COALESCE(
      (
        SELECT MAX(uc.cum_amount)
        FROM user_cum uc
        WHERE uc.user_id = c.user_id
          AND uc.dsi <= d.day - 1
      ),
      0.0
    ) AS cum_through_day
  FROM cohort_users c
  CROSS JOIN days d
)

SELECT
  cost_date AS cohort_cost_date,
  day AS arpu_day,
  COUNT(*) AS n_users_in_cohort,
  COUNTIF(cum_through_day > 0) AS n_depositors_by_day,
  ROUND(SUM(cum_through_day), 2) AS sum_cum_revenue_usd,
  ROUND(SUM(cum_through_day) / COUNT(*), 4) AS arpu_usd
FROM per_user_at_day
GROUP BY cost_date, day
ORDER BY day;
