# Trim & populations cheat sheet (from Combined reference)

Inherited from predecessor Combined notebooks — not re-decided yet.

## Quick map — ARPU curve trim (Combined production)

| Population | RealPrize | LoneStar |
|------------|-----------|----------|
| **Web** | winsor **1%** | winsor **0%** (off) |
| **App** | winsor **0%** (off) | not in pipeline yet |
| **Affiliate** | winsor **1%** | winsor **1%** |
| **Blended** | winsor **0%** (off) | winsor **0%** (off) |
| **PPC** | no ARPU curve (only in organic-share denominator) | same |
| **Organic** | no ARPU curve (used in organic-share as organic bucket) | same |

**Winsor 0%** = method is still “winsor”, but `pct = 0` means **no capping** (same as no trim for that population).

**Cohort trim is not used in Combined production** for any population. It only appears in TrimComparison lab notebooks.

## Organic-share trim (separate from ARPU curves)

| | RealPrize | LoneStar |
|--|-----------|----------|
| Method | winsor | winsor |
| Pct | **0%** (off) | **0%** (off) |

## When does trim run?

On every **patch** while building the ARPU curve (1→7, 7→14, …), for that population’s configured method/pct.

- Mode: **persistent** — if cohort_trim ever drops a user, they stay out of later patches. Winsor does not drop users; it caps revenue each time.
- Then adaptive **CV** may drop outlier *cohort dates* (not the same as trim).

## Winsor vs cohort_trim (reminder)

| | Winsor | Cohort trim |
|--|--------|-------------|
| Action | Cap whale revenue at (1−pct) quantile of depositors | Remove top pct of depositors |
| Users in denominator | Unchanged | Shrinks |
| Used in Combined today? | **Yes** (table above) | **No** (labs only) |

## Who gets goals output?

Combined builds goals for: **Web, App (RP only), Affiliate, + Blended**.

- Per-pop goals: adjusted by organic share  
- Blended goals: raw ratio only (no organic adjustment)
