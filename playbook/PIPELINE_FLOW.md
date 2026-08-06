*Lee Jerusalmy*

# Marketing goals pipeline — RealPrize + LoneStar

Same machinery for both brands. Production run loops **RP then LS** (or either alone via `RUN_BRANDS`) into one goals table with a `brand` column.

**Readable Google Doc** (plain language; started as LS, appendix covers shared knobs for both):  
https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit

**Numeric toy walkthrough (RP Web):** `WORKED_EXAMPLE_RP_WEB.md`  
**Knob / trim map:** `CONFIG_AND_KNOBS.md`

Chart path (both brands):  
brand → population → cum/DSI → ARPU per patch → winsor → growth → CV → weighted day growth → ARPU D1 → curve → (+ organic share) → adjust with organic? → [LS only: extrapolate tail?] → adjusted goal.

### Quick answers

1. **Winsor only for ARPU_e?** No. Cap is **set** from depositors’ cum at patch end **e**, then **applied** when summing cums at **both** s and e (and day-steps). Users stay in N.
2. **CV growth = only ARPU_e / ARPU_s?** Yes. CV ranks/removes **cost_dates** using patch growth `ARPU_e/ARPU_s` only — not day-to-day steps (those come after, on kept dates).

---

## Shared settings (both brands)

| Setting | Value | Notes |
|---------|--------|------|
| as_of_date | today − 2 days | Cohort maturity anchor |
| Lookback | **35** cost_dates per patch | `LOOKBACK_COHORTS` |
| Patches | (1,7) … (270,365) | Same list |
| Goal horizons | 7 … **365** | Day-by-day goals, not monthly-only |
| CV good enough (stop removing) | **0.10** | Both |
| Max dates removable | **15%** | ~5 of 35 |
| Organic-share trim | winsor **0%** (off) | Both |
| Cohort_trim in production | **No** | Labs only |
| Day index | life day D → dsi ≤ D−1 | Both |

`id > 0` always. Cost-per-user tables already exclude test/marketing accounts.

---

## Brand settings (side by side)

| Setting | RealPrize | LoneStar |
|---------|-----------|----------|
| Cost table | `analytics.realprize_cost_per_user` | `analytics.lonestar_cost_per_user` |
| Deposits | `realprize.casino_astropay_dmn` | `lonestar.casino_astropay_dmn` |
| Exclude affids | **4313** (TikTok) | **4866, 7127** |
| Curve populations | Web, **App**, Affiliate + Blended | Web, Affiliate + Blended (**no App** yet) |
| Web winsor | **1%** | **0%** (off) |
| App winsor | **0%** | n/a |
| Affiliate winsor | **1%** | **1%** |
| Blended winsor | **0%** | **0%** |
| CV flag line | **0.15** | **0.175** |
| min_cohort_dates | **1** | **20** |
| Organic share cap | pin at horizon **120** | **None** |
| Tail extrapolate | **No** | **Yes** (~30 day-steps) |
| Users SQL scope/bucket | **Yes** (app / non_app) | **No** → organic `scope=all` |

Full detail: `CONFIG_AND_KNOBS.md`.

---

## Box 1 — Brand

Unified Combined runs `RUN_BRANDS = ['realprize', 'lonestar']`.  
For each brand: `apply_brand_globals` → load tables → Parts 1–4 (curves → Blended → organic → goals).  
Same recipe; only tables, affid lists, and knobs change (table above).

---

## Box 2 — Population

### What happens (both)

1. Pull users from that brand’s `*_cost_per_user` table.
2. Map each row’s `affid` → a population label.
3. One row per user: `MIN(cost_date)` = **cohort date** (the clock for all later ARPU).  
   **Not** registration date (`dateReg`).

### RealPrize affid → label (simplified)

| Population | Affids (representative) | Own ARPU curve? | Goals? |
|------------|-------------------------|-----------------|--------|
| **Web** | 63, 2521, 2535, 4957, 4971, 5048, 5062, 5069 | Yes | Yes |
| **App** | 1 | Yes | Yes |
| **Affiliate** | everything else not listed elsewhere | Yes | Yes |
| **PPC** | 64, 71 | No | Blended + organic *acquired* |
| **Organic** | 0, 78, 2290 | No | Organic share *organic* + Blended |
| **Blended** | all together | Yes | Yes, **no** organic haircut |

RP also assigns `scope` (app if affid=1 else non_app) and `bucket` (organic/acquired) for organic share.

### LoneStar affid → label

| Population | Affids | Own ARPU curve? | Goals? |
|------------|--------|-----------------|--------|
| **Web** | 63, 4432, 4551, 4698, 5048, 5125, 7120, 7253, 7260, 8331, 8345 | Yes | Yes |
| **Affiliate** | everything else (not listed below) | Yes | Yes |
| **PPC** | 64, 71 | No | Only via Blended + organic *acquired* |
| **Organic** | 0, 78 | No | Only via organic-share *organic* + Blended |
| **App** | 1 (commented out) | Not live | — |
| **Blended** | all of the above together | Yes (separate curve) | Yes, **no** organic haircut |

### Scope / bucket (organic later) — plain language

“User structure” here means **what columns the users SQL returns**, not casino DB tables.

**LS Combined today** does **not** pull `scope` / `bucket` columns. Organic share falls back to:

- `scope = 'all'`
- `bucket = organic` if population == Organic, else `acquired`

So Web goals and Affiliate goals on LS currently share one organic-share series.

**RealPrize** pulls both columns in SQL:

- `scope`: `app` (affid=1) vs `non_app`
- `bucket`: organic vs acquired (App organic = affid=1 **and** channel_type app_organic)

Your chart’s **app / non_app** split is the **RP design** (and future LS once App is live). Until then LS Combined = `scope=all`.

Full map: `CONFIG_AND_KNOBS.md` § User structure.
When App is live (RP-style):

| Scope | Populations that use it for the haircut |
|-------|----------------------------------------|
| `non_app` | Web, Affiliate |
| `app` | App |
| Blended | forced organic = 0 |

### Filters at this stage

- `id > 0`
- Exclude brand TikTok affids (RP **4313**; LS **4866, 7127**)
- Cost table already has test/marketing = 0

### Q&A locked in

- PPC / Organic: **no own goal curves**.
- Blended: everyone in one curve.
- Cohort clock: **cost_date**.
- RP: full scope/bucket columns; LS: organic share uses `scope=all` until App lands.

---

## Box 3 — Cum deposits per DSI

### What happens

1. Pull approved deposits; convert cents → dollars (`/ 100`).
2. Join deposit `playerid` → user `id`.
3. Compute  
   `dsi = deposit_date − cost_date` (calendar days).
4. Keep only `dsi ≥ 0` (deposits on/after cost_date). Pre-cost deposits are out of ARPU.
5. Per user, sort by dsi and build **cumulative $**.

### Day indexing (critical)

**“ARPU at day D” uses deposits with `dsi ≤ D − 1`.**

| Goal day D | Max dsi included |
|------------|------------------|
| 1 | 0 |
| 7 | 6 |
| 14 | 13 |
| 30 | 29 |

So day 14 is **not** “through the 14th dsi index”; it stops at dsi 13.

### Tiny user example

User cost_date = Jul 10:

| deposit_date | dsi | amount | cum |
|--------------|-----|--------|-----|
| Jul 10 | 0 | 10 | 10 |
| Jul 12 | 2 | 5 | 15 |
| Jul 16 | 6 | 5 | 20 |

- Day 1 ingredient = **$10** (dsi ≤ 0)  
- Day 7 ingredient = **$20** (dsi ≤ 6)

### Q&A locked in

- Cum is per **user**, then summed for cohort ARPU.
- Same dsi rule for every later box (winsor, growth, organic, goals).

---

## Box 4 — ARPU each patch

### What a “patch” is

A window **(s → e)** on the life-day axis, e.g. **1 → 7**.

Patches exist so that, for each life stage, the pipeline can:

1. Decide which **cost_dates** are mature enough (reached day **e**).
2. Set winsor caps at day **e**.
3. Judge outlier dates on multi-day growth (`ARPU_e / ARPU_s`), not noisy single days.
4. Then (later) estimate **day-to-day** steps inside that window for the curve.

### Who is eligible for patch s→e

Only cost_dates that can already observe day **e**:

- `cohort_end = as_of − e days`
- `cohort_start = as_of − (e + lookback − 1) days`
- ≈ **35** dates ending at `cohort_end`

Example: as_of = Jul 28, patch 1→7 → need dates through Jul 21, lookback 35 days before that.

### Per cost_date (before winsor)

```
N_users     = count of users on that cost_date (in this population)
sum_cum_s   = sum of (each user’s cum $ through day s)   # dsi ≤ s−1
sum_cum_e   = sum of (each user’s cum $ through day e)   # dsi ≤ e−1
ARPU_s      = sum_cum_s / N_users
ARPU_e      = sum_cum_e / N_users
growth      = ARPU_e / ARPU_s     # if ARPU_s > 0
```

Zero-deposit users stay in **N_users** (they pull ARPU down). That is intentional.

### Why not skip patches and only do day-to-day?

You *could* estimate every single day without patches, but then every day would need its own maturity window, cap day, and outlier rule. Patches give a **stable frame**; day-steps give the **shape**.

---

## Box 5 — Winsor? (by population)

### Production settings (Combined)

| Population | RealPrize | LoneStar |
|------------|-----------|----------|
| **Web** | winsor **1%** | winsor **0%** (off) |
| **App** | winsor **0%** | not in pipeline |
| **Affiliate** | winsor **1%** | winsor **1%** |
| **Blended** | winsor **0%** | winsor **0%** |

**Cohort_trim is not used in Combined production** (only in TrimComparison lab notebooks).

### How winsor works (when pct > 0, e.g. Aff 1%)

1. At patch **end day e**, look at users with cum_e > 0 (**depositors only** for the percentile).
2. Cap = quantile at `(1 − pct)` → for 1%, ~**p99**.
3. For every user, replace cum $ with `min(cum, cap)` when summing for ARPU (at s and at e **and** day-steps for that patch).
4. **Users are not removed** from N_users.

**Where in code (Combined helpers):**

- Config chooses method: `BRAND_CONFIGS[…]['trim_config']` → global `TRIM_CONFIG`
- Router: `get_trimmed_cohort_and_caps` → winsor branch builds caps; user list unchanged
- Dollars leave the calc only in `sum_cum_at_idx`: `cum = min(cum, cap_e)`
- Cohort_trim would shrink `trimmed_users` and set `newly_excluded`; production path does not

Detail: `TRIM_BY_POPULATION.md`, `CONFIG_AND_KNOBS.md`.

### Winsor vs cohort_trim (for memory)

| | Winsor | Cohort trim |
|--|--------|-------------|
| Action | Cap whale $ | Drop top pct of depositors |
| Denominator | Unchanged | Shrinks |
| Combined LS/RP today | **Yes** (where pct > 0) | **No** |

### Persistent trim

- **cohort_trim:** if a user is ever dropped, they stay out of later patches (`excluded_uids` grows).
- **winsor:** does not drop users; only caps. “Persistent” barely changes anything for LS Web/Blended (0%) or Aff winsor.

### Q&A locked in

- Caps are computed in the **patch end day e** context.
- Teaching examples sometimes used a fake “$100 cap”; production uses the real quantile of that cohort’s depositors.

---

## Box 6 — ARPU after winsor

Same formulas as Box 4, but sums use **capped** cum $.

```
ARPU_s_w = sum_cum_s_capped / N_users
ARPU_e_w = sum_cum_e_capped / N_users
growth_w = ARPU_e_w / ARPU_s_w
```

For LS **Web** / **Blended** and RP **App** / **Blended**, this equals pre-winsor ARPU (pct = 0).  
For RP **Web**, RP/LS **Affiliate** (winsor 1%), whales no longer dominate growth as much.

---

## Box 7 — Growth

### Patch-level growth (this box → feeds CV)

For each **cost_date** in the patch:

`growth_ratio = ARPU_e / ARPU_s` (after winsor)

You now have ~35 growth numbers (one per date). That cloud of numbers is what CV cleans.

### This is not yet the curve

The curve does **not** jump from day 1 to day 7 using only this one ratio.  
It uses **day-to-day** steps (Box 9).  
Patch growth is for **cleaning + diagnostics**; day-steps are for **shape**.

(If day-steps are consistent, their product over days 2…7 is close to the patch growth for that date.)

---

## Box 8 — CV cleanup (per patch)

### Correct formula (fix the chart if needed)

\[
\mathrm{CV} = \frac{\sigma_w}{\mu_w}
\]

where \(\mu_w\) and \(\sigma_w\) are the **weighted** mean and std of `growth_ratio` across cost_dates.  
**Weight for each date = `sum_cum_s`** (total $ at patch start).

**Not** \(\mu/\sigma\). CV is “noise relative to the mean,” so std ÷ mean.

### Hard-coded knobs (both brands)

| Knob | RealPrize | LoneStar | Meaning |
|------|-----------|----------|---------|
| CV good enough (stop remove) | **0.10** | **0.10** | Same |
| CV flag after cleanup | **0.15** | **0.175** | Warning only; patch still used |
| Max remove fraction | **0.15** | **0.15** | ~5 of 35 dates |
| min_cohort_dates (after CV) | **1** | **20** | Skip patch if too few dates left |

Ranking: worst first by |growth − **unweighted** mean of growths|; then recompute weighted CV after each drop.

These are **config constants**, not estimated from data. See `CONFIG_AND_KNOBS.md`.

### How dates are chosen for removal (order)

1. Compute **unweighted** mean of growths: `mu_unw`.
2. For each cost_date: `abs_dev = |growth − mu_unw|`.
3. Sort dates **largest abs_dev first** (worst outliers first).
4. Before removing anyone, compute **weighted** CV of all dates.
5. If CV ≤ 0.10 → **remove nothing**.
6. Else remove the worst date, recompute weighted CV on the remainder.
7. Repeat until CV ≤ 0.10 **or** you hit the max removable count.

With 35 dates, max removable = `floor(35 × 0.15) = 5`.

### What happens in the 0.10 – flag band?

After stop (either CV ≤ 0.10 or max removes):

| Final cv_after | RealPrize | LoneStar |
|----------------|-----------|----------|
| ≤ flag line | not flagged | not flagged |
| > 0.15 (RP) / > 0.175 (LS) | **flagged** (still used) | **flagged** (still used) |
| 0.10 < cv ≤ flag | not flagged (couldn’t fully clean) | same |

If CV already ≤ 0.10 before any drop → remove nobody.

### Does the script remove dates at all?

**Yes**, whenever starting weighted CV > 0.10.  
Only if CV is already ≤ 0.10 at the start does it remove nobody.

### Grain

- CV is **one number per patch** (not per life-day).
- What gets removed are **cost_dates** for that patch.
- Those dates stay out of **all** day-steps inside that patch (e.g. days 2…7 for patch 1→7).

### Toy example

Growths: 2.13, 1.50, 1.50, **15.0**, 1.50  

Unweighted mean ≈ 4.33 → date with 15 is farthest → removed first → CV of the rest drops → stop.  
Weighted mean of kept ≈ uses `sum_cum_s` weights (next box / diagnostics).

### If we hit the 5-date limit — then what?

Plain-language flow (also in the Google Doc twin):

1. Compute `cv_before` (weighted σ/μ of patch growth).
2. If CV already **≤ 0.10** → remove nobody.
3. If CV **> 0.10** → drop worst cost_dates one by one (max **~5** of 35).
4. Stop at **≤ 0.10** or **hit the 5-date cap**.
5. **Always keep the patch** and build curve/goals from remaining dates.
6. Only then: if `cv_after` **> brand flag** (LS **0.175**, RP **0.15**) → `flagged=True` (warning only).

**Do not remove / skip the life patch** just because it is flagged.  
High `cv_after` after max drops = still noisy after allowed cleanup, not “delete 14→30.”

How to read `combined_cv_summary`: `cv_before` / `cv_after` / `flagged` / kept vs removed cost_dates.

---

## Box 9 — Weighted mean growth (per day)

### Two related averages (don’t confuse them)

| Kind | When | Per what | Weight | Used for |
|------|------|----------|--------|----------|
| **Patch growth mean** | After CV | One `ARPU_e/ARPU_s` per kept cost_date | `sum_cum_s` ($ at patch **start**) | CV diagnostics / `mean_after` |
| **Day-step mean** | For the curve | One `ARPU_k / ARPU_{k−1}` per kept cost_date, for each life-day k | $ at day **k−1** (`sum_prev`) | Stitching the curve |

Your chart label **“per day”** correctly points at the **curve** path.

### Day-step calculation (detail)

For patch **s→e**, on **CV-kept** cost_dates only (and after winsor caps for that patch):

- For patch 1→7, days **k = 2, 3, 4, 5, 6, 7**
- For patch 7→14, days **k = 8 … 14**
- etc.

Per cost_date for day k:

```
ARPU_prev = sum_cum(day k−1) / N
ARPU_curr = sum_cum(day k)   / N
step      = ARPU_curr / ARPU_prev
```

Then:

```
growth_step_k = weighted_mean(step, weights = sum_cum at day k−1)
```

### How D2 is calculated (FAQ)

D2 is **inside** patch 1→7 — there is no separate “1→2” patch.

1. On kept 1→7 dates: each date’s `ARPU_2 / ARPU_1`
2. Weighted average → `growth_step_2`
3. Curve: `ARPU_nominal(2) = ARPU_nominal(1) × growth_step_2`

Same idea for D3, …, D7; then patch 7→14 takes over for D8+.

### Why weight by $ at previous day?

Growth is a multiplier on money already on the board. A cohort with more $ at day k−1 is a more material observation of “how much did ARPU grow into day k?”

### Tiny weighted-mean example (patch growth style)

| cost_date | growth | weight (`sum_cum_s`) |
|-----------|--------|----------------------|
| A | 2.133 | 800 |
| B | 1.500 | 200 |
| C | 1.500 | 200 |
| D | 1.500 | 200 |

Weighted mean = (2.133×800 + 1.5×200×3) / 1400 ≈ **1.861**  
(Simple mean would be ~1.66 — big early-$ date pulls harder.)

---

## Box 10 — ARPU D1 (anchor)

### What it is

The starting dollar level of the stitched curve — **not** taken from a single cohort date.

### Exact Combined rule (first effective patch, usually 1→7)

1. Take first patch’s cohort window (same maturity/lookback as that patch).
2. Drop cost_dates **CV-removed** on that first patch.
3. Drop users excluded by persistent trim as of that patch (winsor usually none).
4. Apply winsor caps from first patch **end** day (e.g. day 7) when pct > 0.
5. Sum all kept users’ **day-1** cum $ (`dsi ≤ 0`).
6. Divide by **total kept users**.

\[
ARPU_1 = \frac{\sum \text{day‑1 \$}}{\sum N_{\text{users}}}
\]

### Important: different weighting than growth

Day-1 anchor = **pooled dollars / pooled users**  
(= average of per-date day-1 ARPUs **weighted by user count**).

It is **not** weighted by `sum_cum_s` the way growth CV is.

### Tiny example

| cost_date | kept? | users | day-1 $ | date ARPU |
|-----------|-------|-------|---------|-----------|
| Jul 10 | yes | 100 | 4000 | 40 |
| Jul 11 | yes | 50 | 1000 | 20 |
| Jul 13 | no (CV) | — | — | — |

`ARPU_1 = 5000/150 ≈ $33.33`  
(not (40+20)/2 = 30).

---

## Box 11 — Curve

### Stitch

```
ARPU_nominal(1)   = ARPU_1
ARPU_nominal(2)   = ARPU_1 × growth_step_2
ARPU_nominal(3)   = ARPU_nominal(2) × growth_step_3
…
ARPU_nominal(7)   = … (still patch 1→7 steps)
ARPU_nominal(8)   = ARPU_nominal(7) × growth_step_8   # patch 7→14
…
ARPU_nominal(365) = … through last patch
```

### What “ARPU_nominal” means

The **model curve** after averaging many dates and stitching patches —  
**not** “ARPU of one cost_date on one day.”

### Outputs at this stage

- `*_arpu_curve.csv` — day, ARPU_nominal, growth_step, effective_patch, …
- `*_cv_summary.csv` — per patch CV before/after, removed dates, flagged, …

### Horizons vs curve length

- Curve is built through **day 365**.
- Goals later **slice** that curve at many horizons (7, 30, …, 365).
- So: full-year engine; multiple goal lengths on top — not a single monthly product.

### Curve tail extrapolation (`is_extrapolated`)

**Where it lives:** after the stitched ARPU curve (fill-forward of late life $ days).  
**On your chart:** after “adjust with organic?” → decision **Need extrapolation?** Yes/No → adjusted goal.  

Code vs chart: Combined extends the **ARPU curve** when the last measured day is before 365; goals then only **divide** those ARPUs. Organic haircut is separate. The chart box is the “do late days need fill?” gate; it is not a second goal formula.  
Goals never compute a special “True” formula.

**Why it exists:**  
Long horizons (e.g. 365) need ARPU at late life days. Patches only measure days that **mature cohorts already reached**. If the stitched curve’s last real day is **before** 365, Combined (LS) can **extend** the curve forward. Those filled days are marked `is_extrapolated = True`.

**Not “no history at all.”**  
Extension uses the **last ~30 measured days already on the curve**. Without at least 2 real days, there is nothing to extend from and the function returns the curve unchanged.

#### What `is_extrapolated` means when you read a row

| Value | Meaning |
|-------|---------|
| **False** | ARPU for that life day came from measured patch growth (history). |
| **True** | ARPU for that life day was **filled forward** with a constant daily growth rate — not observed at that day. |

#### Formula (LS Combined — `extrapolate_curve_tail`)

Defaults in predecessor: `up_to_day=365`, `tail_days=30`.

1. Let `last_real_day` = max day on the **non-extrapolated** curve.  
   If already ≥ 365 → do nothing.
2. Take the last `tail_days` real rows:  
   `ARPU_nominal` for days near the end of the measured curve.
3. Day-to-day growth ratios on that tail:  
   `ratio_d = ARPU(d) / ARPU(d−1)` (keep finite, &gt; 0).
4. One constant daily rate = **geometric mean** of those ratios:  
   `r = exp(mean(log(ratios)))`  
   (= average multiplicative step, not arithmetic mean of the ratios).
5. Walk forward:  
   `ARPU(last_real_day + 1) = ARPU(last_real_day) × r`  
   `ARPU(last_real_day + 2) = that result × r`  
   … up to day 365.  
   Each new row: `is_extrapolated = True`, `growth_step = r`.

#### Tiny example

Measured curve ends at day 100 with ARPU = **$10**.  
Last ratios in the tail average (geometrically) to **r = 1.01** (+1%/day).

| day | ARPU | is_extrapolated |
|-----|------|-----------------|
| 100 | 10.00 | False |
| 101 | 10.00 × 1.01 = 10.10 | **True** |
| 102 | 10.10 × 1.01 = 10.201 | **True** |
| … | × 1.01 each day | **True** |

#### Goals when a curve day is extrapolated

Same formulas as always:

```text
raw_goal_ratio      = ARPU(day) / ARPU(goal_horizon)
adjusted_goal_ratio = raw_goal_ratio × (1 − organic_share)
```

`is_extrapolated` is an **audit flag** copied onto the goal row (when present).  
It does **not** change the goal algebra — only whether the ARPU inputs were measured or filled.

If **day** and/or **goal_horizon** fall on True days, that goal ratio inherits that weaker late-life assumption.

#### LS vs RP (predecessor Combined)

| Brand | Tail fill in Combined |
|-------|------------------------|
| **LoneStar** | `extrapolate_curve_tail` present — filled days get `is_extrapolated = True`. |
| **RealPrize** | Column often exists and is set **False** for stitched days; full tail-fill not the same production path as LS. Treat RP as “flag reserved / usually False unless we enable the same helper.” |

#### Q&A locked in

- Goals box ≠ prediction box. Prediction (fill-forward) = **curve stage only**.
- Early goals (7, 14, 30…) are almost always on **False** days if patches cover them.
- Year-1 **horizon** may use a **True** denominator if late life was filled — check the flag on day 365 / late days when reading long goals.

---

## Box 12 — Organic share (side branch from population)

### Purpose

Separate question from the ARPU curve:  
**Of deposit dollars in this scope, what fraction is organic?**

Marketing uses that to haircut paid-channel goals (so goals aren’t credited for organic volume).

### Formula

\[
organic\_share = \frac{\text{organic cum \$}}{\text{organic cum \$} + \text{acquired cum \$}}
\]

at a chosen **checkpoint** day. For goals, Combined keeps only rows where  
`checkpoint_day == goal_horizon` (the **endpoint**).

Example: horizon 30 → cum through day 30 (`dsi ≤ 29`) only.  
That one share is reused for **every day** inside the 30-day goal (day 1 and day 7 get the same organic %).

### Buckets

| Bucket | LS (today) | RP / future App-style |
|--------|------------|------------------------|
| organic | population = Organic (affid 0, 78) | + App with `channel_type = app_organic` |
| acquired | everyone else in scope (Web, Aff, PPC, …) | same idea |

PPC counts as **acquired**. Organic population as **organic**.

### Eligibility window

Same idea as patches: for horizon H, only cohorts mature enough for day H, lookback 35.

### Trim on organic share (LS)

winsor **0%** → no capping in the organic-share stage.

### LS vs your chart labels

| Your chart | LS Combined today | When App is live / RP |
|------------|-------------------|------------------------|
| Web → non_app | Web → **scope `all`** (same number as Aff) | Web → `non_app` |
| Aff → non_app | Aff → **scope `all`** | Aff → `non_app` |
| App → app | N/A | App → `app` |
| Blended → 0 | Yes, forced 0 | Same |

### RP-only quirk (not LS)

RP pins horizons **> 120** to the organic share measured at 120 (App attribution change).  
**LS has no such cap** in Combined.

### Excel check

`playbook/sql_steps/06_organic_share_non_app_h30_rp.sql` is the RP-style check.  
For LS, same math with LS tables / affid map and typically `scope = all`.

---

## Box 13 — Adjust with organic?

| Population | Apply organic haircut? | Which share |
|------------|------------------------|-------------|
| **Web** | Yes | LS today: `all`; chart/RP: `non_app` |
| **Affiliate** | Yes | same as Web’s scope |
| **App** | Yes when live | `app` |
| **Blended** | **No** — organic forced to **0** | — |

---

## Box 14 — Adjusted goal (final deliverable)

### Formulas

**Web / Affiliate / (App):**

```
raw_goal_ratio      = ARPU_nominal(day) / ARPU_nominal(horizon)
adjusted_goal_ratio = raw_goal_ratio × (1 − organic_share_at_horizon)
```

**Blended:**

```
adjusted_goal_ratio = raw_goal_ratio
# organic_share stored as 0
```

No separate formula when `is_extrapolated` is True — goals only divide curve ARPU points  
(see **Box 11 → Curve tail extrapolation**).

### Grain of the output

One row per:

`population × goal_horizon × day`  
with `day` from 1 … `goal_horizon`.

Example meanings:

| Row | Meaning |
|-----|---------|
| Web, horizon 30, day 7 | By day 7, what % of day-30 ARPU (after organic) |
| Web, horizon 90, day 30 | By day 30, what % of day-90 ARPU |
| Web, horizon 365, day 180 | By day 180, what % of year-1 ARPU |
| Blended, horizon 30, day 7 | Same pace idea, **no** organic haircut |

### Teaching example (numbers fake, structure real)

| Input | Value |
|-------|-------|
| ARPU day 7 | $5 |
| ARPU day 30 | $20 |
| raw | 5/20 = **0.25** |
| organic_share @ 30 | **0.20** |
| adjusted | 0.25 × 0.80 = **0.20** |

→ “On a 30-day goal, by day 7 expect 20% of horizon ARPU after organic haircut.”

### Output files (Combined)

| File | Contents |
|------|----------|
| `*_goals_adjusted.csv` | **Main deliverable** |
| `*_arpu_curve.csv` | Nominal $ curve |
| `*_organic_share.csv` | Share by scope × horizon × checkpoint |
| `*_cv_summary.csv` | Patch CV / removals / flags |

---

## End-to-end checklist (chart order)

```text
LS filters + affid map
    ↓
population + cost_date
    ↓
deposits → dsi → cum $          ──┐
    ↓                             │
for each patch s→e:               │
    eligible ~35 cost_dates       │
    ARPU_s, ARPU_e                │
    winsor by pop (LS: Aff 1%)   │
    growth = ARPU_e/ARPU_s        │
    CV: drop outlier cost_dates   │
    day-steps  (k−1)→k weighted   │
    ↓                             │
ARPU_1 pooled from first patch    │
    ↓                             │
multiply day-steps → Curve        │
    ↓ (optional LS)               │
extend tail if last day < 365     │
  is_extrapolated = True on fill  │
                                  │
organic share (from population)  ←┘
    ↓
adjust? (Web/Aff yes, Blended 0)
    ↓
Need extrapolation? (chart Yes/No — fill already on curve if needed)
    ↓
adjusted goals (many horizons × every day)
```

---

## Chart corrections / clarifications

1. **CV formula:** use **σ/μ ≤ 0.10** to stop; flag if **> 0.175** (LS). Not μ/σ.
2. **Growth box:** patch growth feeds CV; **per-day** weighted steps feed the curve.
3. **Organic “non_app” on LS today:** Combined uses **`scope=all`** until App/scope columns exist; your chart is the right *target design* for App launch / RP parity.
4. **Goals are not only monthly:** curve to 365; horizons include 7, 30, 60, …, 365; each horizon is day-by-day.
5. **`is_extrapolated` / chart “Need extrapolation?”:** Yes = late life days on the ARPU curve were filled forward (geom. mean of last ~30 daily steps); those days = True. Goals still only divide ARPU points — see Box 11.

---

## Related playbook files

- `METHODOLOGY.md` — short pipeline overview  
- `TRIM_BY_POPULATION.md` — RP vs LS trim cheat sheet  
- `WORKED_EXAMPLE_RP_WEB.md` — numeric walkthrough (RP Web)  
- `sql_steps/` — Excel verification SQL  
- `config/lonestar.yaml` — knobs
