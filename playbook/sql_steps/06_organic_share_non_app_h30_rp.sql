-- Step 06 — RealPrize: organic share (non_app, horizon 30, endpoint checkpoint)
-- What this proves: share = organic_$ / (organic_$ + acquired_$) at day 30
--   for cohorts mature enough for a 30-day horizon (lookback 35), matching Combined.
-- Production organic trim is winsor 0% → no capping here.
-- Goals use ONLY checkpoint_day = goal_horizon (here 30), not intermediate 7/14.
--
-- Cost note: one horizon × one scope. Cheap.

DECLARE as_of DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY);
DECLARE horizon INT64 DEFAULT 30;
DECLARE lookback INT64 DEFAULT 35;  -- LOOKBACK_COHORTS

WITH users AS (
  SELECT
    id AS user_id,
    DATE(MIN(cost_date)) AS cost_date,
    CASE WHEN affid = 1 THEN 'app' ELSE 'non_app' END AS scope,
    CASE
      WHEN affid = 1 AND channel_type = 'app_organic' THEN 'organic'
      WHEN affid = 1 THEN 'acquired'
      WHEN affid IN (0, 78, 2290) THEN 'organic'
      ELSE 'acquired'  -- Web, Affiliate, PPC
    END AS bucket
  FROM `analytics.realprize_cost_per_user`
  WHERE cost_date >= DATE_SUB(as_of, INTERVAL horizon + lookback - 1 DAY)
    AND affid != 4313
    AND id > 0
  GROUP BY id, scope, bucket
),

-- Cohorts that can already reach day `horizon`
elig AS (
  SELECT *
  FROM users
  WHERE scope = 'non_app'
    AND cost_date BETWEEN DATE_SUB(as_of, INTERVAL horizon + lookback - 1 DAY)
                      AND DATE_SUB(as_of, INTERVAL horizon DAY)
),

deposits AS (
  SELECT
    playerId AS user_id,
    DATE(date) AS dep_date,
    SUM(amount) / 100.0 AS amount
  FROM `realprize.casino_astropay_dmn`
  WHERE Status = 'APPROVED'
    AND date >= DATE_SUB(as_of, INTERVAL horizon + lookback - 1 DAY)
    AND amount > 0
  GROUP BY 1, 2
),

joined AS (
  SELECT
    e.user_id,
    e.bucket,
    e.cost_date,
    DATE_DIFF(d.dep_date, e.cost_date, DAY) AS dsi,
    d.amount
  FROM elig e
  INNER JOIN deposits d ON d.user_id = e.user_id
  WHERE DATE_DIFF(d.dep_date, e.cost_date, DAY) BETWEEN 0 AND horizon - 1  -- dsi ≤ 29 for day 30
),

-- Per-user cum through checkpoint (day 30 endpoint)
user_cum AS (
  SELECT
    user_id,
    bucket,
    cost_date,
    SUM(amount) AS cum_cp
  FROM joined
  GROUP BY user_id, bucket, cost_date
),

-- Users with $0 still count in user counts; $ only from depositors
with_zeros AS (
  SELECT
    e.user_id,
    e.bucket,
    e.cost_date,
    IFNULL(u.cum_cp, 0.0) AS cum_cp
  FROM elig e
  LEFT JOIN user_cum u
    ON u.user_id = e.user_id
   AND u.bucket = e.bucket
   AND u.cost_date = e.cost_date
)

SELECT
  'non_app' AS scope,
  horizon AS goal_horizon,
  horizon AS checkpoint_day,
  MIN(cost_date) AS cohort_start,
  MAX(cost_date) AS cohort_end,
  SUM(IF(bucket = 'organic', cum_cp, 0)) AS organic_sum,
  SUM(IF(bucket = 'acquired', cum_cp, 0)) AS acquired_sum,
  SUM(cum_cp) AS total_sum,
  SAFE_DIVIDE(
    SUM(IF(bucket = 'organic', cum_cp, 0)),
    SUM(cum_cp)
  ) AS organic_share,  -- same as org / (org + acq) when only those two buckets
  COUNTIF(bucket = 'organic') AS users_org,
  COUNTIF(bucket = 'acquired') AS users_acq
FROM with_zeros;
