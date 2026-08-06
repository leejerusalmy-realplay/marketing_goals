*Lee Jerusalmy*

# Config cell & knobs — RealPrize + LoneStar

**Brands:** both run from one Combined config cell (`RUN_BRANDS`). Shared calendar; per-brand dict under `BRAND_CONFIGS`.

| Notebook | Role |
|----------|------|
| `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` | Colab |
| `notebooks/Marketing_Goals_Combined_RP_LS.ipynb` | Cursor / local twin |

YAML mirrors (not loaded at runtime — keep in sync by hand):

| Brand | File |
|-------|------|
| RealPrize | `config/realprize.yaml` |
| LoneStar | `config/lonestar.yaml` |

Plain-language Doc: https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit

---

## How dual-brand works

1. Config defines shared constants + full knobs for **each** brand.
2. Globals seed from RP first (so helpers define).
3. Pipeline loop: for each brand in `RUN_BRANDS` → `apply_brand_globals(cfg)` **overwrites** `TRIM_CONFIG`, `CV_*`, `MIN_COHORT_DATES`, etc. → load tables → Parts 1–4.
4. Outputs stamped with `brand` column and often combined in one pack.

If LS runs without `apply_brand_globals`, it wrongly keeps RP knobs.
---

## What the config cell is

Pure **control panel** — no data pull. Defines:

1. Shared calendar (`AS_OF_DATE`, patches, horizons, lookback)
2. Which brands run (`RUN_BRANDS`)
3. Per-brand knobs (`BRAND_CONFIGS`)
4. Monitoring previews
5. Seed globals used by helper functions until `apply_brand_globals` overwrites them

---

## Shared calendar

| Knob | Value | Meaning |
|------|--------|---------|
| `AS_OF_DATE` | today − 2 days (midnight) | Cohort maturity anchor for the whole run |
| `PATCHES` | (1,7), (7,14), … (270,365) | Frames for maturity, winsor end-day, patch-level CV |
| `GOAL_HORIZONS` | 7, 30, 60, … 365 | Goal rows: day / horizon ratios |
| `CHECKPOINTS` | same list as horizons | Organic-share measurement days |
| `LOOKBACK_COHORTS` | **35** | Target # of mature `cost_date`s per patch window |
| `ORGANIC_LABEL` | `'Organic'` | Population name treated as organic when no `bucket` column |

---

## Per-brand knobs (side by side)

| Knob | RealPrize | LoneStar |
|------|-----------|----------|
| Cost table | `analytics.realprize_cost_per_user` | `analytics.lonestar_cost_per_user` |
| Deposits | `realprize.casino_astropay_dmn` | `lonestar.casino_astropay_dmn` |
| Exclude affids | `4313` (TikTok) | `4866`, `7127` |
| Curve populations | Web, App, Affiliate (+ Blended later) | Web, Affiliate (+ Blended) |
| Web winsor | **1%** | **0%** (off) |
| App winsor | **0%** | n/a (not in pipeline) |
| Affiliate winsor | **1%** | **1%** |
| Blended winsor | **0%** | **0%** |
| Organic-share trim | winsor **0%** | winsor **0%** |
| Organic share cap horizon | **120** (pin share above D120) | **None** |
| `cv_threshold` (flag after cleanup) | **0.15** | **0.175** |
| `cv_good_enough` (stop removing dates) | **0.10** | **0.10** |
| `max_remove_fraction` | **0.15** (~5 of 35 dates) | same |
| `min_cohort_dates` | **1** | **20** |
| `extrapolate_tail` | **False** | **True** (last ~30 day-steps) |
| `has_scope_bucket` | **True** | **False** |

---

## `min_cohort_dates` (nuance learned 2026-08)

After adaptive CV on a patch, if the number of **cohort cost_dates** left for that patch is **below** this gate → **skip the patch** (no step ratios; patch does not contribute to the curve).

| Brand | Value | Practical meaning |
|-------|--------|-------------------|
| RP | **1** | Almost never blocks; even a single remaining cost_date can form a patch. |
| LS | **20** | Stricter: need ≥ 20 cost_dates in the window (post-gates) or the patch is skipped. |

This is a count of **acquisition days** (`cost_date`), not users.

Code path: first pass of `build_curve` checks `stats['n_cohort_dates_total'] < MIN_COHORT_DATES`.

---

## User structure: `scope` / `bucket` (not “DB schema”)

This is only about **which columns the users SQL returns**, so **organic share** can be computed correctly.

### RealPrize — `has_scope_bucket = True`

Users SQL includes:

| Column | How set |
|--------|---------|
| `population` | Web / App / Affiliate / Organic / PPC from affid |
| `scope` | `app` if affid = 1, else `non_app` |
| `bucket` | `organic` if (App + channel_type app_organic) or organic affids; else `acquired` |

Organic share is measured **within scope** (e.g. Web goals use **non_app** organic vs acquired dollars). App organic is separate from web organic.

### LoneStar — `has_scope_bucket = False`

Users SQL only has `population` + `cost_date` (no scope/bucket columns).

Helpers then set:

| Field | Default |
|-------|---------|
| `scope` | always **`all`** |
| `bucket` | `organic` if `population == ORGANIC_LABEL` (`'Organic'`), else `acquired` |

So today Web and Affiliate **share the same organic share number** for LS (`scope=all`). Chart labels “non_app / app” match **RP** (or future LS App), not current LS Combined.

Full flow: `PIPELINE_FLOW.md` Box 2 + organic boxes; Google Doc STEP 2 / 12.

---

## Trim methods — production vs lab

See full cheat sheet: `TRIM_BY_POPULATION.md`.

| Method | Effect on users | Effect on $ | Combined production |
|--------|-----------------|-------------|---------------------|
| **winsor** | Keep all users in N | Cap cum: `min(cum, cap_e)` | **Yes** (all pops) |
| **cohort_trim** | Drop top % of depositors | Their $ entirely gone | **No** (labs only) |
| winsor **pct = 0** | Keep all | Cap = ∞ (no effect) | Yes (RP App/Blended, LS Web/Blended, organic stage) |

### Where the method is chosen (config)

In each brand under `BRAND_CONFIGS[…]['trim_config'][population]`:

```text
'Web': {'method': 'winsor', 'pct': 0.01}   # or 0
```

Also mirrored in `config/realprize.yaml` / `config/lonestar.yaml`.

### Where the method is applied (code)

`get_trimmed_cohort_and_caps` (helpers cell — “trimming & cohort revenue summation”):

```text
cfg = TRIM_CONFIG.get(population, default cohort_trim 10%)
if method == 'winsor'       → compute_winsor_caps; trimmed = full cohort
if method == 'cohort_trim'  → apply_cohort_trim; caps = None
```

**Default if population missing from TRIM_CONFIG:** `cohort_trim` 10% (user drop). Named populations today all set explicitly to winsor.

### Where $ exclusion shows up for winsor (not user drop)

In `sum_cum_at_idx`:

```text
if caps is not None:
    per_user['cum'] = min(cum, cap_e)
```

User stays in `cohort_users` / `N_users`. Only dollars above the cap leave the numerator.

### Where user exclusion would show up (cohort_trim only)

1. `apply_cohort_trim` returns `keep` list without top depositors.
2. `patch_cv_adaptive` uses `trimmed_users` for `N_users` and for `sum_cum_at_idx`.
3. `newly_excluded = set(cohort) − set(trimmed_users)` — **empty under winsor**.
4. Debug fields: `n_users_pre_trim` vs `n_users_post_trim` equal ⇒ no user drop.

### Cap day vs day of sum (nuance)

- Winsor **cap** is computed at patch **end day e** (depositors’ cum through dsi ≤ e−1).
- Same cap is applied when summing **day s and day e and every day-step** inside that patch.
- Cap is **not** recomputed per life-day.

Quantile uses **depositors only** (`cum_e > 0`); zeros don’t pull p99 down.

### “Persistent trim” print line

Notebook prints: `Mode: PERSISTENT TRIM (excluded users carry forward)`.

- Under **cohort_trim**: dropped uids enter `excluded_uids` and stay out of later patches.
- Under production **winsor**: almost no user exclusions; “persistent” is historical / lab language. CV still drops **cost_dates** (different layer).

---

## Seed globals & brand switch

At bottom of config cell, globals are seeded from **RP** so helper defs resolve names.

Before each brand run, `apply_brand_globals(cfg)` overwrites:

`POPULATIONS`, `TRIM_CONFIG`, organic trim knobs, `CV_*`, `MIN_COHORT_DATES`, `EXTRAPOLATE_TAIL`, etc.

If you forget this for LS, helpers would incorrectly use **RP** knobs.

---

## Colab / Combined cell map (reading order)

| Cell / block | Contents |
|--------------|----------|
| Auth / BQ / Drive | Colab only |
| **Config** | This file’s knobs |
| apply_brand + load_brand_tables | Brand SQL users + deposits |
| Helpers — math & cums | weighted CV; per-user cum by dsi |
| Helpers — trim & sum | winsor / cohort_trim / `sum_cum_at_idx` |
| Adaptive CV | `patch_cv_adaptive` |
| Curve builder | two-pass persistent trim + optional LS tail |
| Organic share | scope × horizon; endpoint share for goals |
| Part 4 + pipeline | goals; Parts 1–4 run order |
| RUN / PREVIEW / EXPORT | both brands → CSVs under `runs/` |

Pipeline Parts 1–4 (per brand): pop curves → Blended → organic → goals.

Locked goals columns:  
`brand`, `population`, `goal_horizon`, `day`, `raw_goal_ratio`, `organic_share`, `adjusted_goal_ratio`

---

## Monitoring knobs

| Knob | Meaning |
|------|---------|
| `MONITOR_STEPS` | Print intermediate tables after each Part |
| `MONITOR_PREVIEW_DAYS` | ARPU milestone days shown in previews |
| `MONITOR_PREVIEW_HORIZONS` | Goal sample horizons only |

---

## Related playbook files

| File | What |
|------|------|
| `TRIM_BY_POPULATION.md` | Per-pop method table + winsor vs trim |
| `METHODOLOGY.md` | End-to-end formula summary |
| `PIPELINE_FLOW.md` | Every chart box (RP + LS technical) |
| `WORKED_EXAMPLE_RP_WEB.md` | Numeric RP Web path |
| `sql_steps/08_*` | Full patch 1→7 pre/post winsor SQL parity |
| `DECISIONS.md` | Dated locks |
| Google Doc | Plain-language LS guide + appended nuances |
