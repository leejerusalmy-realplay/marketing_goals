-- Step 02c — Can deposits happen before cost_date? (dsi < 0)
-- What this proves: empirically, for id > 0 in a recent window, approved deposits
--   are never before MIN(cost_date). Registration (dateReg) CAN be before cost_date.
-- cost_date = marketing attribution / cost allocation date, not always = registration.

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date,
    MIN(first_deposit_date) AS first_deposit_date_tbl,
    MIN(dateReg) AS date_reg
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
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
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY)
  GROUP BY 1, 2
),

joined AS (
  SELECT
    u.user_id,
    u.cost_date,
    d.deposit_date,
    DATE_DIFF(d.deposit_date, u.cost_date, DAY) AS dsi,
    d.amount
  FROM users u
  INNER JOIN deposits d ON d.user_id = u.user_id
)

-- A) Deposit vs cost_date
SELECT
  'deposit_vs_cost' AS check_name,
  COUNT(*) AS n_rows,
  COUNTIF(dsi < 0) AS n_dsi_lt_0,
  COUNT(DISTINCT IF(dsi < 0, user_id, NULL)) AS n_users_dsi_lt_0,
  ROUND(SUM(IF(dsi < 0, amount, 0)), 2) AS revenue_dsi_lt_0
FROM joined

UNION ALL

-- B) Table fields vs cost_date (no astropay join)
SELECT
  'table_ftd_reg_vs_cost' AS check_name,
  COUNT(*) AS n_rows,
  COUNTIF(first_deposit_date_tbl < cost_date) AS n_dsi_lt_0,  -- FTD before cost
  COUNTIF(date_reg < cost_date) AS n_users_dsi_lt_0,           -- reg before cost
  NULL AS revenue_dsi_lt_0
FROM users;
