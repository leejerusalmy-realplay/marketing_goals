*Lee Jerusalmy*

# Full worked example — RealPrize Web (toy numbers)

**Brands in project:** RP + LS share the same math.  
**This file only:** **RealPrize · Web** with **simplified teaching numbers** so every formula is hand-checkable.

| This file | Not this file |
|-----------|----------------|
| Toy users / ARPU / one goal path | Real BQ extract or Colab run |
| RP Web knobs (winsor 1%, flag 0.15, …) | LS knobs — see table below |
| Learning aid | Excel ground truth → use `sql_steps/` |

**If you need LoneStar:** same steps; change tables + knobs from the table.  
**Real SQL (RP Web fixture):** `sql_steps/08a`–`08d`.  
**Full pipeline:** `PIPELINE_FLOW.md` · **All knobs:** `CONFIG_AND_KNOBS.md`

### Knobs used in this example vs what LS would use

| Setting | This file (RP Web) | LoneStar Web (for comparison) |
|---------|--------------------|--------------------------------|
| Brand / tables | RealPrize | LoneStar tables |
| Population | Web | Web |
| Winsor | **1%** | **0%** (numbers = “pre-winsor” style) |
| CV flag | 0.15 | 0.175 |
| min_cohort_dates | 1 | 20 |
| Organic scope for Web goals | **non_app** | **all** |
| Organic pin @ 120 | yes (if horizon long) | no |
| Tail extrapolate | no | yes if curve short |
| Exclude affid | 4313 | 4866, 7127 |
| Web affids | 63, 2521, 2535, 4957, 4971, 5048, 5062, 5069 | LS web list (see CONFIG) |

---

## 0. Fixed settings used in this example

| Setting | Value |
|--------|--------|
| Brand | RealPrize |
| Population | Web |
| as_of_date | 2026-07-28 (today − 2) |
| Patch shown in detail | **1 → 7** |
| Lookback | 35 cohort dates (we show 5 for clarity) |
| Winsor | **1%** (Web RP) |
| CV: good enough / flag / max remove | 0.10 / 0.15 / 15% of dates |
| Goal we finish on | horizon **30**, day **7** |
| Organic share (assumed measured) | **20%** for non_app @ horizon 30 |

---

## 1. Who enters the data pull (filters)

From `analytics.realprize_cost_per_user` + `realprize.casino_astropay_dmn`:

| Filter | Rule | Why |
|--------|------|-----|
| Real player | `id > 0` | Drop negative/junk ids |
| Not TikTok | `affid != 4313` | Excluded population |
| Already in cost table | test_account = 0, marketing_account = 0 | Built into that table |
| Date floor | `cost_date ≥ as_of − 405 days` | Need history for long patches |
| Deposits | `Status = 'APPROVED'`, amount `/100` = USD | Revenue definition |
| dsi | deposit on/after cost_date only (`dsi ≥ 0`) | No pre-cost deposits in ARPU |

**Web affid list:** 63, 2521, 2535, 4957, 4971, 5048, 5062, 5069.

Only users with those affids go into the **Web** curve.  
PPC / Organic are **not** in the Web curve (they appear later in organic share / Blended).

---

## 2. One user — dsi and cumulative $

User `U1`, Web, `cost_date = 2026-07-10`.

| deposit_date | dsi | amount $ | cum $ |
|--------------|-----|----------|-------|
| 2026-07-10 | 0 | 10 | 10 |
| 2026-07-12 | 2 | 5 | 15 |
| 2026-07-16 | 6 | 5 | **20** |

- **Day 1 ARPU ingredient for this user** = cum through dsi ≤ 0 → **$10**  
- **Day 7 ARPU ingredient** = cum through dsi ≤ 6 → **$20**

---

## 3. One cohort date — ARPU before winsor

Cohort = all Web users with `cost_date = 2026-07-10` (say **4 users**):

| user | cum day 1 (dsi≤0) | cum day 7 (dsi≤6) |
|------|-------------------|-------------------|
| U1 | 10 | 20 |
| U2 | 0 | 8 |
| U3 | 0 | 0 |
| U4 (whale) | 50 | **500** |

**Before winsor:**

- Sum day 1 = 10+0+0+50 = **60** → ARPU_s = 60/4 = **$15.00**  
- Sum day 7 = 20+8+0+500 = **528** → ARPU_e = 528/4 = **$132.00**  
- growth = 132/15 = **8.80** (whale-dominated — this is why winsor exists)

---

## 4. Winsor 1% on this cohort (at patch end day 7)

Among **depositors** (cum day 7 > 0): U1=20, U2=8, U4=500.  
(For a real cohort with hundreds of depositors, p99 is a high percentile.  
Here, for teaching, pretend **p99 cap = $100**.)

| user | raw cum day 7 | after winsor |
|------|---------------|--------------|
| U1 | 20 | 20 |
| U2 | 8 | 8 |
| U3 | 0 | 0 |
| U4 | 500 | **100** (capped) |

Same cap is applied when summing day 1 for this patch (cap from cum@e):

| user | raw cum day 1 | after winsor |
|------|---------------|--------------|
| U1 | 10 | 10 |
| U2 | 0 | 0 |
| U3 | 0 | 0 |
| U4 | 50 | 50 (under cap) |

**After winsor:**

- Sum day 1 = 60 → ARPU_s = **$15.00**  
- Sum day 7 = 20+8+0+100 = **128** → ARPU_e = 128/4 = **$32.00**  
- growth = 32/15 = **2.133**

Users are **not removed** (winsor ≠ cohort trim). Only $ is capped.

**Important:** Cap is recomputed **per cost_date** and **per patch end e**.  
Patch 1→7 uses day-7 cums; patch 30→60 would use day-60 cums for its p99.

---

## 5. Many cohort dates → growth list (patch 1→7)

**Not only 2026-07-10.**  
Section 3–4 walked **one** cost_date in detail so you could see winsor → ARPU_s → ARPU_e → growth.

For the patch, Combined repeats that **same math for every mature cost_date** in the window  
(~35 dates: about **2026-06-17 … 2026-07-21** when as_of = 2026-07-28).

So the growth table below is **many cohorts side by side**.  
The row **2026-07-10 / growth 2.133** is exactly what we calculated in §4 — one row among many.

We show **5** dates after winsor (real run ≈ 35):

| cost_date | N users | ARPU_s (day 1) | ARPU_e (day 7) | growth = e/s | weight (sum $ at s) | where from? |
|-----------|---------|----------------|----------------|--------------|---------------------|-------------|
| 2026-07-10 | 4 | 15.00 | 32.00 | **2.133** | 60 | **§4 detail** |
| 2026-07-11 | 100 | 2.00 | 3.00 | **1.500** | 200 | same recipe, other users |
| 2026-07-12 | 80 | 2.50 | 3.75 | **1.500** | 200 | same recipe |
| 2026-07-13 | 90 | 1.80 | **27.00** | **15.000** | 162 | same recipe (outlier) |
| 2026-07-14 | 110 | 2.20 | 3.30 | **1.500** | 242 | same recipe |

Each row’s ARPU_s / ARPU_e is **that cost_date’s own users only** — not mixed with other dates yet.

---

## 6. CV outlier cleanup — remove bad cost_dates

Idea: growth ratios should not jump wildly across dates.

1. Compute weighted mean of growth (weight = sum cum at s).  
2. Rank dates by |growth − mean|.  
3. Drop worst dates until CV is low enough, **max 15%** of dates.  
   With 5 dates → max remove floor(5×0.15)=0… in real 35-date window max remove ≈ 5 dates.  
   Here we **force-remove the obvious outlier** for teaching: **2026-07-13** (growth 15.0).

**After removal:**

| cost_date | growth | weight | kept? |
|-----------|--------|--------|-------|
| 2026-07-10 | 2.133 | 60 | yes |
| 2026-07-11 | 1.500 | 200 | yes |
| 2026-07-12 | 1.500 | 200 | yes |
| 2026-07-13 | 15.000 | 162 | **NO** |
| 2026-07-14 | 1.500 | 242 | yes |

**Weighted mean growth of KEPT dates only:**

\[
\frac{2.133\times60 + 1.5\times200 + 1.5\times200 + 1.5\times242}{60+200+200+242}
= \frac{127.98 + 300 + 300 + 363}{702}
= \frac{1090.98}{702}
\approx \mathbf{1.554}
\]

July 13 does **not** enter this average.

In `cv_summary.csv` you would see something like:

- `n_cohort_dates_total = 5` (35 in real runs)  
- `n_cohort_dates_kept = 4`  
- `removed_dates = 2026-07-13`  
- `mean_after ≈ 1.554`  
- `flagged = False` if CV after cleanup ≤ 0.15  

---

## 7. Where does ARPU_nominal on the curve come from?

**Not** equal to one cohort’s ARPU_e (e.g. July 10’s $32).

July 10’s $32 is only “what that one cost_date looked like at day 7.”  
The **curve** is a **blended model** built like this:

1. Take **kept** cost_dates only (after CV) for patch 1→7.  
2. **Start (day 1):** pool those cohorts → one shared ARPU day 1  
   (total capped $ on day 1 ÷ total users).  
3. **Days 2…7:** multiply by day-to-day growth steps, each step also  
   averaged from the **same kept** dates (winsor still on).  
4. Later patches (7→14, 14→30, …) continue the line with their own windows.

### Mini stitch consistent with §5–6 (kept dates only)

Pooled day-1 ARPU from kept dates (teaching weights):

| cost_date | users | ARPU_s | contrib $ (= users × ARPU_s) |
|-----------|-------|--------|------------------------------|
| 07-10 | 4 | 15.00 | 60 |
| 07-11 | 100 | 2.00 | 200 |
| 07-12 | 80 | 2.50 | 200 |
| 07-14 | 110 | 2.20 | 242 |
| **Total** | **294** | | **702** |

Curve day 1 = 702 / 294 ≈ **$2.39**

If day-to-day steps over days 2…7 compound to the same ~1.554 patch growth:

Curve day 7 ≈ 2.39 × 1.554 ≈ **$3.71**

*(In the real notebook, day-to-day steps are estimated separately per day,  
so day 7 won’t be exactly day1 × patch growth — but it’s the same idea.)*

Then patches 7→14 and 14→30 continue until day 30.  
For the **goal section below**, we use a simple finished curve so the division is easy to read:

| day | ARPU_nominal | meaning |
|-----|--------------|---------|
| 1 | 2.39 | from pooled kept cohorts (§7) |
| 7 | **5.00** | after stitching (rounded teaching value) |
| 30 | **20.00** | after later patches (teaching value) |

So: **ARPU_nominal = curve output after averaging/stitching many dates**,  
not “the ARPU of 10/7/26 alone.”

---

## 8. Organic share (separate stage)

Not from the Web-only curve. Measured on organic vs acquired deposit buckets  
(for Web goals, RP uses **non_app** scope).

Example measurement at horizon 30 endpoint:

| | |
|--|--|
| Organic deposit $ in window | 200,000 |
| Acquired deposit $ | 800,000 |
| **organic_share** | 200k/(200k+800k) = **0.20** |

PPC counts in **acquired**. Organic population in **organic**.  
This 0.20 is reused for **every day** inside the 30-day Web goal.

---

## 9. Goal calculation (Web, horizon 30, day 7)

From the curve:

| Input | Value |
|-------|-------|
| ARPU_nominal (day 7) | $5.00 |
| ARPU_at_horizon (day 30) | $20.00 |
| raw_goal_ratio | 5/20 = **0.25** (25%) |
| organic_share | **0.20** |
| adjusted_goal_ratio | 0.25 × (1−0.20) = **0.20** (20%) |

### Output row (as in `*_goals_adjusted.csv`)

| column | value |
|--------|-------|
| population | Web |
| goal_horizon | 30 |
| day | 7 |
| ARPU_nominal | 5.00 |
| ARPU_at_horizon | 20.00 |
| raw_goal_ratio | 0.25 |
| organic_share | 0.20 |
| adjusted_goal_ratio | **0.20** |
| effective_patch | 1→7 |
| is_extrapolated | False |

**Meaning:** For RealPrize Web, on a 30-day goal, by day 7 expect to reach **20%** of horizon ARPU after organic haircut.

---

## 10. End-to-end checklist (what happened where)

```text
FILTERS: id>0, not TikTok, Web affid, approved deposits, dsi≥0
    ↓
CUM $ by user by dsi
    ↓
FOR PATCH 1→7 (and every other patch):
    per cost_date (~35):
        WINSOR at day e → ARPU_s, ARPU_e → growth
    CV: drop outlier cost_dates
    weighted avg / day-steps on KEPT dates only
    ↓
STITCH patches → ARPU curve (nominal $)
    ↓
ORGANIC SHARE (separate)
    ↓
GOAL: day$ / horizon$ × (1 − organic)
    ↓
CSV outputs
```

---

## 11. What we skipped only for length (same logic)

- All other patches (7→14 … 270→365) with older cohort windows  
- App / Affiliate / Blended curves (same machinery; different winsor %)  
- Full 35-date CV math (same remove-and-average idea)  
- LS differences (no App; Web winsor 0%; CV threshold 0.175)

---

## 12. Files this maps to

| Stage | Output file |
|-------|-------------|
| Winsor + CV per patch | `*_cv_summary.csv` |
| Stitched $ curve | `*_arpu_curve.csv` |
| Organic % | `*_organic_share.csv` |
| Final goals | `*_goals_adjusted.csv` |
