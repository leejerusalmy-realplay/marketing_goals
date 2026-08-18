*Lee Jerusalmy*

# Goal-120 realized check — freeze 2026-07-10

Same two engines as the April check. New calendar. **Not** a methodology lock.
Does not change generic Combined or `DECISIONS.md`.

## Question

If Combined (and capped winsor_escalation) had been run on **2026-07-10**,
do the frozen H=120 daily goals match what we can already see through
**2026-08-17**?

## Dates (Lee, 2026-08-18)

| Choice | Value |
|--------|--------|
| Goals freeze `AS_OF_DATE` | **2026-07-10** (10/07/26) |
| Eval cost_dates | **2026-07-10 … 2026-08-17** |
| Last deposit / last observed day | **2026-08-17** (pinned; not “today”) |
| Training | cost_date and deposits **before** 2026-07-10 |

## What this is not

Day 120 is **not** complete. Oldest eval users (cost_date 10 Jul) have **39**
life days on 17 Aug. The April primary (`ARPU(d) / ARPU(120)`) cannot be used.

## How we score (this check only)

- Actuals still **raw** (no winsor). $0 users stay in N. No fill of missing days.
- Frozen goals are still H=120 Combined math (patches through 120).
- **Primary = shape so far**, on a **fixed user set** (same N every day):
  - actual `ARPU(d) / ARPU(D*)` vs frozen `ARPU_nominal(d) / ARPU_nominal(D*)`
  - `first_day` (10 Jul only): **D* = 39** — main engine compare
  - `first_5_days` (10–14 Jul): **D* = 35** — same idea as the April 5-day wave
- `overall_level` (all arrivals 10 Jul–17 Aug): **dollars only**, and only for
  users who have already lived that day. Do **not** read shape here — N changes
  by day.

RP Web will likely still be thin. Not a lock.

## Engines

1. Production Combined (`notebooks/Marketing_Goals_Combined_RP_LS.ipynb`)
2. Capped winsor_escalation (15% absolute revenue-cut stop) + `pct_used` wired
   into the curve (same as the April variant)

## How to run

**Colab:** `goal120_july_colab.ipynb` — run top → bottom. Runs **both** engines.

Local:

```bash
python "experiments/goal120_realized_2026-07-10/run_goal120_july.py"
```

One engine only: `--engine production` or `--engine winsor_esc`.

## Export

`runs/2026-07-10_rp_ls_goal120_realized_<HHMMSS>/`  
`runs/2026-07-10_rp_ls_goal120_realized_winsor_esc_<HHMMSS>/`

Eye compare after both finish: `compare_vs_production.csv` (filter
`slice = first_day`). Lower `shape_mae` = closer pace so far.
