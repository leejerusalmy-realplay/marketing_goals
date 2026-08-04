-- Step 07 — Goal ratio from ARPU curve + organic share (toy numbers)
-- What this proves (no live BQ tables — free to run):
--   1) raw_goal_ratio      = ARPU_nominal(day) / ARPU_nominal(horizon)
--   2) adjusted_goal_ratio = raw × (1 − organic_share)  for Web/Aff/App
--   3) Blended: organic forced to 0 → adjusted = raw
--   4) Within a horizon, organic is the ENDPOINT share only (same for every day)
--   5) RP quirk: horizons > 120 pin organic to the day-120 share (LS has no cap)
--
-- Numbers match playbook/examples/SAMPLE_realprize_combined_goals_adjusted.csv
--   and WORKED_EXAMPLE_RP_WEB.md §9 (Web / H30 / day 7).
--
-- Excel check:
--   • Export this result
--   • Or skip BQ: open SAMPLE_*_goals_adjusted.csv and recompute
--       raw  = ARPU_nominal / ARPU_at_horizon
--       adj  = raw × (1 − organic_share)   [Blended: adj = raw]
--   • Spot-check at least: Web·30·7 → raw 0.25, adj 0.20
--                          Blended·30·7 → raw = adj ≈ 0.2143
--                          Web·180·30 → uses organic@120 = 0.22, not 0.25

WITH
-- Minimal stitched curve (teaching values only)
arpu_curve AS (
  SELECT * FROM UNNEST([
    STRUCT('Web' AS population, 1 AS day, 0.63 AS ARPU_nominal),
    STRUCT('Web', 7, 5.00),
    STRUCT('Web', 14, 10.00),
    STRUCT('Web', 30, 20.00),
    STRUCT('Web', 120, 55.00),
    STRUCT('Web', 180, 70.00),
    STRUCT('App', 7, 8.50),
    STRUCT('App', 30, 40.00),
    STRUCT('Affiliate', 7, 3.20),
    STRUCT('Affiliate', 30, 18.00),
    STRUCT('Blended', 7, 6.00),
    STRUCT('Blended', 30, 28.00)
  ])
),

-- Organic share at each (scope-like) measurement horizon.
-- Goals only look up share where checkpoint = goal_horizon (endpoint).
-- Intermediate checkpoints (7, 14 inside H=30) exist in organic files but are NOT used for goals.
organic_by_horizon AS (
  SELECT * FROM UNNEST([
    STRUCT('non_app' AS scope, 7 AS goal_horizon, 0.18 AS organic_share),
    STRUCT('non_app', 30, 0.20),
    STRUCT('non_app', 120, 0.22),
    STRUCT('non_app', 180, 0.25),  -- real measurement at 180 — RP goals will IGNORE this
    STRUCT('app', 30, 0.15)
  ])
),

-- Which scope feeds which population for the haircut
pop_scope AS (
  SELECT * FROM UNNEST([
    STRUCT('Web' AS population, 'non_app' AS scope, FALSE AS force_organic_zero),
    STRUCT('Affiliate', 'non_app', FALSE),
    STRUCT('App', 'app', FALSE),
    STRUCT('Blended', CAST(NULL AS STRING), TRUE)  -- always haircut off
  ])
),

-- Goal cells to build: population × horizon × day  (small demo set)
goal_cells AS (
  SELECT * FROM UNNEST([
    STRUCT('Web' AS population, 30 AS goal_horizon, 1 AS day),
    STRUCT('Web', 30, 7),
    STRUCT('Web', 30, 14),
    STRUCT('Web', 30, 30),
    STRUCT('Web', 7, 1),
    STRUCT('Web', 7, 7),
    STRUCT('App', 30, 7),
    STRUCT('Affiliate', 30, 7),
    STRUCT('Blended', 30, 7),
    -- RP organic-cap demo (compare organic_measured vs organic_used)
    STRUCT('Web', 180, 30),
    STRUCT('Web', 180, 180)
  ])
),

joined AS (
  SELECT
    g.population,
    g.goal_horizon,
    g.day,
    c_day.ARPU_nominal,
    c_h.ARPU_nominal AS ARPU_at_horizon,
    ps.scope,
    ps.force_organic_zero,
    -- Share *measured* at this horizon (if it exists)
    o_h.organic_share AS organic_share_measured_at_horizon,
    -- RP pin: horizons > 120 use share@120; LS Combined does not pin (would keep measured)
    o_120.organic_share AS organic_share_at_120,
    CASE
      WHEN ps.force_organic_zero THEN 0.0
      WHEN g.goal_horizon > 120 THEN o_120.organic_share   -- RP only
      ELSE o_h.organic_share
    END AS organic_share_used
  FROM goal_cells g
  JOIN pop_scope ps
    ON ps.population = g.population
  JOIN arpu_curve c_day
    ON c_day.population = g.population
   AND c_day.day = g.day
  JOIN arpu_curve c_h
    ON c_h.population = g.population
   AND c_h.day = g.goal_horizon
  LEFT JOIN organic_by_horizon o_h
    ON o_h.scope = ps.scope
   AND o_h.goal_horizon = g.goal_horizon
  LEFT JOIN organic_by_horizon o_120
    ON o_120.scope = ps.scope
   AND o_120.goal_horizon = 120
)

SELECT
  population,
  goal_horizon,
  day,
  ARPU_nominal,
  ARPU_at_horizon,
  ROUND(SAFE_DIVIDE(ARPU_nominal, ARPU_at_horizon), 6) AS raw_goal_ratio,
  organic_share_measured_at_horizon,
  organic_share_at_120,
  organic_share_used AS organic_share,
  CASE
    WHEN force_organic_zero THEN TRUE
    WHEN goal_horizon > 120
     AND organic_share_measured_at_horizon IS DISTINCT FROM organic_share_used
    THEN TRUE
    ELSE FALSE
  END AS organic_override_note,  -- TRUE = Blended0 or RP pin from 120
  ROUND(
    SAFE_DIVIDE(ARPU_nominal, ARPU_at_horizon) * (1.0 - IFNULL(organic_share_used, 0.0)),
    6
  ) AS adjusted_goal_ratio,
  CASE
    WHEN population = 'Web' AND goal_horizon = 30 AND day = 7 THEN 'expect raw=0.25 adj=0.20'
    WHEN population = 'Blended' AND goal_horizon = 30 AND day = 7 THEN 'expect raw=adj≈0.214286'
    WHEN population = 'Web' AND goal_horizon = 180 AND day = 30
      THEN 'RP: share used=0.22 not 0.25; adj = (30/70)×0.78'
    ELSE NULL
  END AS excel_spot_check
FROM joined
ORDER BY
  CASE population
    WHEN 'Web' THEN 1 WHEN 'App' THEN 2 WHEN 'Affiliate' THEN 3 ELSE 4
  END,
  goal_horizon,
  day;
