*Lee Jerusalmy*

# Trim & populations cheat sheet (from Combined reference)

Inherited from predecessor Combined notebooks — locked in `config/*.yaml` and `BRAND_CONFIGS` in Combined notebooks.  
Full config map: **`CONFIG_AND_KNOBS.md`**.

## Quick map — ARPU curve trim (Combined production)

| Population | RealPrize | LoneStar |
|------------|-----------|----------|
| **Web** | winsor **1%** | winsor **0%** (off) |
| **App** | winsor **0%** (off) | not in pipeline yet |
| **Affiliate** | winsor **1%** | winsor **1%** |
| **Blended** | winsor **0%** (off) | winsor **0%** (off) |
| **PPC** | no ARPU curve (only in organic-share denominator) | same |
| **Organic** | no ARPU curve (used in organic-share as organic bucket) | same |

**Winsor 0%** = method is still “winsor”, but `pct = 0` means **no capping** (cap = ∞; same as no trim for that population).

**Cohort trim is not used in Combined production** for any population. It only appears in TrimComparison lab notebooks.

## Do we “trim users”?

| Production method | Answer |
|-------------------|--------|
| **winsor** (all live pops) | **No.** User stays in N. Only revenue above the cap is excluded from the sum. |
| **cohort_trim** (labs) | **Yes.** Top % of depositors by cum at day **e** are removed from the cohort. |

“Top % of depositors” ≠ “top % of the whole cohort” — percentile is among users with cum_e > 0.

## Organic-share trim (separate from ARPU curves)

| | RealPrize | LoneStar |
|--|-----------|----------|
| Method | winsor | winsor |
| Pct | **0%** (off) | **0%** (off) |

## When does trim run?

On every **patch** while building the ARPU curve (1→7, 7→14, …), for that population’s configured method/pct.

- Mode: **persistent** — if cohort_trim ever drops a user, they stay out of later patches (`excluded_uids`). Winsor does not drop users; it caps revenue each time.
- Then adaptive **CV** may drop outlier *cohort dates* (not the same as trim).

## Winsor vs cohort_trim (reminder)

| | Winsor | Cohort trim |
|--|--------|-------------|
| Action | Cap whale revenue at (1−pct) quantile of depositors | Remove top pct of depositors |
| Users in denominator | Unchanged | Shrinks |
| Used in Combined today? | **Yes** (table above) | **No** (labs only) |

## Cap mechanics (winsor) — nuances

1. Cap measured at patch **end day e** from depositors only.
2. Same caps applied to sums at day **s**, day **e**, and every day-step inside the patch (not re-fit per life day).
3. Life day D uses `dsi ≤ D−1` (same as rest of pipeline).
4. `sum_cum_at_idx` applies: `cum = min(cum, cap_e)`.

SQL parity (RP Web 1→7 one cohort): `sql_steps/08c_*` pre-winsor, `08d_*` after winsor 1%.

## Where method is **chosen** (config)

**Notebook** (`BRAND_CONFIGS` config cell):

```text
'trim_config': {
    'Web': {'method': 'winsor', 'pct': 0.01},  # RP
    ...
}
```

**YAML:** `config/realprize.yaml`, `config/lonestar.yaml`  
(Notebooks currently **inline** these — update both if you change knobs.)

Organic stage uses separate knobs: `organic_trim_method`, `organic_trim_pct`.

## Where method is **applied** (code)

Helpers cell “trimming & cohort revenue summation”:

| Function | Role |
|----------|------|
| `compute_winsor_caps` | Build per-user `cap_e` (or ∞ if pct ≤ 0) |
| `apply_cohort_trim` | Return smaller user list (lab path) |
| `get_trimmed_cohort_and_caps` | Router via `TRIM_CONFIG[population]` |
| `sum_cum_at_idx` | Sum revenue for users in the list; apply caps |

Call chain for ARPU/CV (in `patch_cv_adaptive`):

```text
trimmed_users, caps = get_trimmed_cohort_and_caps(...)
N_users  from trimmed_users
sum_s/e  = sum_cum_at_idx(..., cohort_users=trimmed_users, caps=caps)
```

Under winsor: `trimmed_users` = full cohort, `newly_excluded` empty, pre/post user counts match.

**Fallback if population missing from TRIM_CONFIG:** defaults to **cohort_trim 10%** — so every production population must stay explicitly in the dict.

## Who gets goals output?

Combined builds goals for: **Web, App (RP only), Affiliate, + Blended**.

- Per-pop goals: adjusted by organic share  
- Blended goals: raw ratio only (no organic adjustment)
