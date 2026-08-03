-- Step 02 — RealPrize: dsi + cumulative deposit revenue (Excel check)
-- What this proves: for each user, deposit day is measured from first cost_date (dsi),
--   amount is USD (/100), and cum_amount is running sum of deposits with 0 <= dsi <= 29
--   (first 30 days only — cheap learning window; full pipeline uses up to day 365).
--
-- Cost: users with cost_date in last 45 days; only 3 sample users per population who deposited.
-- Excel tip: filter to one user_id and check that cum_amount = running sum of amount by dsi.

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date,
    CASE
      WHEN ANY_VALUE(affid) IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069) THEN 'Web'
      WHEN ANY_VALUE(affid) = 1 THEN 'App'
      WHEN ANY_VALUE(affid) IN (64, 71) THEN 'PPC'
      WHEN ANY_VALUE(affid) IN (0, 78, 2290) THEN 'Organic'
      ELSE 'Affiliate'
    END AS population
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY)
    AND affid != 4313
    AND id > 0
  GROUP BY id
),

-- Daily deposit totals (approved), USD
deposits AS (
  SELECT
    playerId AS user_id,
    DATE(date) AS deposit_date,
    SUM(amount) / 100.0 AS amount
  FROM `realprize.casino_astropay_dmn`
  WHERE Status = 'APPROVED'
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 45 DAY)
  GROUP BY 1, 2
),

joined AS (
  SELECT
    u.user_id,
    u.population,
    u.cost_date,
    d.deposit_date,
    d.amount,
    DATE_DIFF(d.deposit_date, u.cost_date, DAY) AS dsi
  FROM users u
  INNER JOIN deposits d
    ON d.user_id = u.user_id
  WHERE DATE_DIFF(d.deposit_date, u.cost_date, DAY) BETWEEN 0 AND 29
),

-- Pick 3 users per population who have at least one deposit in dsi 0–29
sample_users AS (
  SELECT user_id, population
  FROM (
    SELECT
      user_id,
      population,
      ROW_NUMBER() OVER (PARTITION BY population ORDER BY user_id) AS rn
    FROM (SELECT DISTINCT user_id, population FROM joined)
  )
  WHERE rn <= 3
),

daily AS (
  SELECT
    j.user_id,
    j.population,
    j.cost_date,
    j.dsi,
    SUM(j.amount) AS amount_on_dsi   -- if multiple deposit rows same dsi (shouldn't after group), sum
  FROM joined j
  INNER JOIN sample_users s
    USING (user_id, population)
  GROUP BY j.user_id, j.population, j.cost_date, j.dsi
)

SELECT
  user_id,
  population,
  cost_date,
  dsi,
  ROUND(amount_on_dsi, 2) AS amount_on_dsi,
  ROUND(
    SUM(amount_on_dsi) OVER (
      PARTITION BY user_id
      ORDER BY dsi
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ),
    2
  ) AS cum_amount
FROM daily
ORDER BY population, user_id, dsi;
