*Lee Jerusalmy*

# Trim & populations — RealPrize + LoneStar

**Brands:** both. Production method is **winsor** for all live populations.  
**Full knobs:** `CONFIG_AND_KNOBS.md` · **Pipeline boxes:** `PIPELINE_FLOW.md` § winsor

---

## Shared rules

| Rule | Both brands |
|------|-------------|
| Production method | **winsor** (never cohort_trim in Combined goals) |
| Winsor 0% | Cap = ∞ → no effect (still labeled winsor) |
| Cap day | Patch end **e**, depositors-only quantile |
| Cap applied to | Day s, day e, day-steps inside patch |
| Users in N | **Keep all** under winsor |
| Organic-stage trim | winsor **0%** (off) for both |
| PPC / Organic | No own ARPU curve; only Blended + organic share |

Cohort_trim (delete top depositors) exists in code/labs only — not production.

---

## What differs by brand / population

| Population | RealPrize | LoneStar | Effect difference |
|------------|-----------|----------|-------------------|
| **Web** | winsor **1%** | winsor **0%** | RP Web whales capped; LS Web full $ |
| **App** | winsor **0%** | not in pipeline | RP has App curve; LS does not |
| **Affiliate** | winsor **1%** | winsor **1%** | **Same** (p99-style cap) |
| **Blended** | winsor **0%** | winsor **0%** | **Same** (off) |

### Why Web differs

Inherited from Combined predecessors: RP Web has more whale noise → 1% winsor. LS Web runs uncapped (pct 0).

### Who gets goals

| Population | RP | LS |
|------------|----|----|
| Web | yes + organic haircut | yes + organic haircut |
| App | yes + organic haircut | — |
| Affiliate | yes + organic haircut | yes + organic haircut |
| Blended | yes, **raw only** | yes, **raw only** |

Organic haircut uses **scope** (RP: non_app for Web/Aff, app for App; LS: **all** for Web and Aff).

---

## Do we “trim users”?

| Method | Production? | Users | Money |
|--------|-------------|-------|-------|
| **winsor** | **Yes** (all live) | stay in N | `min(cum, cap_e)` |
| **cohort_trim** | **No** (labs) | top depositors dropped | fully out |

“Top %” of **depositors** only (cum_e > 0), not of all users.

---

## Cap mechanics (both brands, when pct > 0)

1. At e: `cum_e` per user (dsi ≤ e−1).
2. Cap = quantile (1 − pct) among depositors in that (population, cost_date).
3. Sums use `min(cum, cap)` in `sum_cum_at_idx`.
4. Under winsor, `n_users_pre_trim == n_users_post_trim`.

SQL parity: RP Web 1% → `sql_steps/08c` (pre) / `08d` (post).  
LS Web is always “pre style” for Web (0% = uncapped).

---

## Where config lives

| Brand | Notebook `BRAND_CONFIGS['…']['trim_config']` | YAML |
|-------|-----------------------------------------------|------|
| RP | Web/Aff 0.01, App/Blended 0 | `config/realprize.yaml` |
| LS | Aff 0.01, Web/Blended 0 | `config/lonestar.yaml` |

Applied via global `TRIM_CONFIG` after `apply_brand_globals`.  
Router: `get_trimmed_cohort_and_caps`.  
Missing pop defaults to cohort_trim 10% — always list every live pop explicitly.

---

## Code path (same both brands)

```text
get_trimmed_cohort_and_caps → winsor caps (or no-op if pct 0)
sum_cum_at_idx(..., caps=caps)  → cum = min(cum, cap_e)
```
