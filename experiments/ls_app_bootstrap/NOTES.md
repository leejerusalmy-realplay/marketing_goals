*Lee Jerusalmy*

# LS App bootstrap notes

## Setup

- Launch: **2026-07-16**
- Experiment home: `experiments/ls_app_bootstrap/`
- Combined Colab (working copy): `Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`
- Frozen archive: `notebooks/versions/v3_2026-08_winsor_esc_ls_app/`
- Python twin (do not run unprompted): `build_winsor_esc_plus_ls_app.py`
- Method compare: `run_ls_app_bootstrap.py`
- Topic handoff: `playbook/handoffs/LS_APP.md`

Provisional — not locked into generic Combined or `DECISIONS.md`.

---

## How to calculate LS App (provisional)

Same Combined boxes through last **measured** history, then a different tail.

1. Map `affid = 1` → population **App**.
2. Cum deposits / dsi / ARPU per patch — same as Combined.
3. Winsor floor **0%** and stays 0% — **no winsor_escalation** on LS App.
4. Growth + CV + day-steps on measured patches only.
5. ARPU D1 = LS App own pooled day-1 ARPU (native pass, before the RP tail).
6. Keep the native curve through last non-extrapolated day **S**.
7. After S, do **not** use LS tail extrapolation. Stick RP App day-growth from the RP winsor_esc curve in the same run:

   `ARPU(d) = ARPU(d-1) × (ARPU_RP_App(d) / ARPU_RP_App(d-1))`

8. Goals: `raw = ARPU(d) / ARPU(H)`.
9. **Organic off for now:** `organic_share = 0` so `adjusted = raw`.
10. **LS Blended stays Web + Affiliate only.** App is an add-on, not folded in.

S is the last patch that actually ran. LS skips a patch if cohort dates &lt; **20** (`min_cohort_dates`).  
S moves later when `AS_OF_DATE` moves and more App cohorts have lived the patch end-day.  
One more month of data → expect **S = 30**, not 60. S = 60 needs ~early October.

RP-style `scope` / `bucket` (`app` vs `non_app`, `app_organic`) is in the users SQL for later. Do **not** apply App organic yet (see below).

---

## Method-compare checks

How we scored: short-horizon **shape so far** on a fixed user set.

- Actual `ARPU(d) / ARPU(D*)` vs frozen `ARPU_nominal(d) / ARPU_nominal(D*)`
- Do not pick the method on horizon-120 fit
- Latest export: `runs/2026-08-17_ls_app_bootstrap_114318/` (~24k App users through 2026-08-17)

Methods tested:

1. `native_ls_app` — full Combined on LS App (including LS tail extrapolate)
2. `ls_web_donor` — LS Web shape × LS App own D1
3. `rp_app_donor` — RP App shape × LS App own D1
4. `hybrid_donor` — average of Web + RP App shape × LS App own D1
5. `native_early_rp_tail` — native through last measured day, then RP App day-growth

| Slice | D* | Leader | Shape MAE | Notes |
|-------|---:|--------|----------:|-------|
| `launch_day` (16 Jul only) | 33 | **rp_app_donor** | 0.274 | native_early 3rd (0.298); native last (0.367) |
| `launch_week` (16–22 Jul) | 27 | **native_early_rp_tail** (tie with native) | 0.083 | identical through D*=27; rp_app last (0.110) |

Frozen ARPU:

| Method | D30 | D120 |
|--------|----:|-----:|
| native_ls_app | 24.77 | **6,855** (broken tail — do not use) |
| native_early_rp_tail | 24.77 | **48.45** |
| ls_web_donor | 21.39 | 48.96 |
| hybrid_donor | 20.23 | 43.14 |
| rp_app_donor | 19.08 | 37.33 |

**Why native_early_rp_tail:** keeps LS App’s own early growth (better on the first-week wave) and only borrows RP App after measured history ends. `rp_app_donor` still wins the oldest single-day cohort but is worse on the first-week wave.

Splice on that compare run: after **day 30**.

---

## Combined Colab run (2026-08-18)

Export: `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`

Base engine: v2 winsor_esc Colab (`notebooks/versions/v2_2026-08_winsor_escalation_combined/`) with `pct_used` wired into the curve.

- `AS_OF_DATE` still pinned **2026-08-03** → App splice **S = 14** (patch 14→30 skipped, &lt;20 cohort dates)
- ~25.8k App users; mapping worked (app acquired 21,467 / app organic 4,326)
- Winsor stayed 0%
- D1 **$6.24** → D14 **$16.97** → D120 **$48.71** (did not explode)
- App organic forced to **0** in the CSVs after the run

This pack is **not** a copy of `runs/2026-08-03_rp_ls_winsor_escalation_143601/`:

- 143601 did not wire `pct_used` into the curve (CV reported escalation; curve stayed on floor winsor)
- This Colab wires `pct_used`, so RP Web / RP App / LS Web move
- `affid=1` left LS Affiliate, so Affiliate (and a bit of Blended level) change
- Close match: RP Affiliate, RP Blended, LS Blended **goal ratios**

---

## Why App organic is off

Organic share is measured only on users who already lived the full horizon H.

With as_of 2026-08-03 (App live since 16 Jul):

| Horizon | What happened | Why |
|---------|----------------|-----|
| H7 | ~60% organic | Real mix of App users with 7 days — high vs RP App |
| H30 | **100%** organic (368 org / 0 acquired) | Window ends 4 Jul, **before** launch; leftover old `affid=1` only |
| H120 | **NaN** | Nobody has 120 App life days yet |

H120 empty is “missing.” H30 at 100% is a **misleading number**, not “the app is all organic.”  
Leave organic off until there is a mature App cohort. Mapping can stay in SQL for later.

---

## Leftover `affid=1` (opened 2026-08-18)

`affid = 1` existed before LS App launch. Combined maps all of it to App.  
Excel SQL: `experiments/ls_app_bootstrap/sql/01_leftover_affid1_vs_app.sql`.

Checked 2026-08-18:

| Era | Users | Distinct cost_dates | Range |
|-----|------:|--------------------:|-------|
| pre-launch leftover | 1,102 | 24 | 2026-03-26 → 2026-07-15 |
| real App | 24,703 | 34 | 2026-07-16 → 2026-08-18 |

Leftover is small in the full file, but it dominates **long** patches (only old cohorts have lived 30 days).

Combined as_of **2026-08-03** (matches the Colab print):

| Patch | Users | Dates | Of which leftover | Launch-floor dates |
|-------|------:|------:|------------------:|-------------------:|
| 1→7 | 5,972 | 34 | 1,095 users / 22 dates | **12** (<20 → would skip) |
| 7→14 | 2,319 | 27 | 1,095 / 22 | **5** |
| 14→30 | 368 | 12 | 368 / 12 (all leftover) | **0** (skipped today) |

Raw D1 in that 1→7 window (first-day $, no CV): leftover **$9.07** vs real App **$4.65** vs pooled **$5.46**. Combined curve D1 was **$6.24**. Leftover is pulling D1 up.

Method-compare splice **S=30** (freeze 2026-08-17) is not 30 days of real App. Patch 14→30 had 1,736 users / 25 dates; **1,095 / 22 dates are leftover**, only 641 users / 3 dates are post-launch.

If App is floored at launch (`cost_date >= 2026-07-16`):

- as_of 2026-08-16 (today−2): 1→7 runs (25 dates); 7→14 skips (18); 14→30 skips (2) → **S = 7**
- S = 14 needs ~20 post-launch dates that have lived 14 days → as_of around **2026-08-18+**
- S = 30 needs those dates to have lived 30 days → as_of around **2026-09-03**

Not applied yet. Do not bump as_of alone and treat S=30 as native App.

---

## How to run

```bash
python "experiments/ls_app_bootstrap/run_ls_app_bootstrap.py" --count-only
python "experiments/ls_app_bootstrap/run_ls_app_bootstrap.py"
```

Colab: open `Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb` → Runtime → Run all.  
Do not run `build_winsor_esc_plus_ls_app.py` unless Lee asks.

Re-score method compare when another ~2 weeks of App cohorts accumulate, or `launch_day` D* reaches ~45+.

Main method-compare file: `method_summary.csv`.  
120-day picture: `WRITEUP.md` + `plot_ls_app_horizon120.png` in the compare export.
