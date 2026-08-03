-- Step 02b — RealPrize: sanity summary of dsi / deposits (cheap)
-- What this proves: deposits join, dsi >= 0 filter, and /100 conversion look sane at aggregate level.
-- Window: cost_date last 45 days; dsi 0–29 only.

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
    u.population,
    u.user_id,
    DATE_DIFF(d.deposit_date, u.cost_date, DAY) AS dsi,
    d.amount
  FROM users u
  INNER JOIN deposits d
    ON d.user_id = u.user_id
)

SELECT
  population,
  COUNT(DISTINCT user_id) AS users_with_any_deposit_row,
  COUNT(DISTINCT IF(dsi BETWEEN 0 AND 29, user_id, NULL)) AS users_with_deposit_dsi_0_29,
  COUNTIF(dsi < 0) AS deposit_rows_before_cost_date,  -- excluded later; should be small
  ROUND(SUM(IF(dsi BETWEEN 0 AND 29, amount, 0)), 2) AS revenue_dsi_0_29_usd,
  ROUND(AVG(IF(dsi BETWEEN 0 AND 29, amount, NULL)), 2) AS avg_daily_deposit_usd
FROM joined
GROUP BY population
ORDER BY population;
