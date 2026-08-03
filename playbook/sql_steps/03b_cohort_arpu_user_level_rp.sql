-- Step 03b — RealPrize: user-level rows for ONE cohort (recompute ARPU in Excel)
-- What this proves: you can filter one day, sum cum_through_day, divide by n_users, match 03.
-- Same cohort pick logic as 03 (Web, latest cost_date >= 30 days old with >= 20 users).

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
    AND affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069)
    AND affid != 4313
    AND id > 0
  GROUP BY id
),

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

days AS (
  SELECT day FROM UNNEST([1, 7, 14, 30]) AS day
)

SELECT
  c.cost_date AS cohort_cost_date,
  c.user_id,
  d.day AS arpu_day,
  ROUND(
    COALESCE(
      (
        SELECT MAX(uc.cum_amount)
        FROM user_cum uc
        WHERE uc.user_id = c.user_id
          AND uc.dsi <= d.day - 1
      ),
      0.0
    ),
    2
  ) AS cum_through_day
FROM cohort_users c
CROSS JOIN days d
ORDER BY d.day, c.user_id;
