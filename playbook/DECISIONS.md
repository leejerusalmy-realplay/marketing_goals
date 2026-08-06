# Decisions (marketing goals)

Dated locks for this project. Newest first.

*(None locked from Excel verification yet for the full pipeline. Values below include build choices from Lee + inherited Combined knobs in `config/`.)*

## 2026-08-06 — Config & trim nuances documented (walkthrough)

Read-through of Combined Colab **config cell** + **trim helpers** locked into playbook:

- **`playbook/CONFIG_AND_KNOBS.md`** — full knob map, seed globals, scope/bucket, min_cohort_dates, where method is chosen/applied.
- **`playbook/TRIM_BY_POPULATION.md`** — expanded with “do we trim users?”, code paths, cap nuances.
- **Google Doc** appended with plain-language twin of the same materials.

Inherited production facts re-confirmed (not newly re-decided):

| Fact | Value |
|------|--------|
| ARPU trim method in Combined | **winsor only** (all pops) |
| cohort_trim in production | **No** (labs only) |
| Winsor **drops users?** | **No** — only `min(cum, cap)`; N unchanged |
| Caps computed at | Patch **end day e**, depositors-only quantile |
| Caps applied to | Day s, day e, and day-steps inside the patch |
| RP `min_cohort_dates` | **1** |
| LS `min_cohort_dates` | **20** |
| RP user shape | scope app/non_app + bucket |
| LS user shape | no scope/bucket columns → organic **scope=all** |
| Config lives in | Notebook `BRAND_CONFIGS` (+ mirrored `config/*.yaml`, not runtime-loaded) |

## 2026-08-04 — Rebuild v1: Colab + Combined structure

- **Engine:** Google **Colab** notebook (v1 entrypoint), not local CLI-only.
- **Code shape:** start from existing Combined structure (`reference/Marketing_Goals_Combined_*.ipynb`) — same pipeline sections/exports spirit — then unify **RP + LS** into **one run / one goals table**.
- **Main goals columns (locked):** `brand`, `population`, `goal_horizon`, `day`, `raw_goal_ratio`, `organic_share`, `adjusted_goal_ratio`. Keep `day` (not dsi).
- **Step 07 Excel:** not done yet; not a blocker to start coding.
- **Where:** `notebooks/` + dated `runs/`; config already in `config/*.yaml`.

## 2026-07-30 — Step 01 locked: population assignment (RP)

- **Verified (Excel + BQ, 14-day window):** affid → population / scope / bucket mapping is solid.
- **Lee finding:** messy multi `cost_date` (and similar) shows up on **`id < 0`**, not on real players.
- **BQ confirm (14d):** `id > 0` → 0 users with multi-affid or multi-cost_date; `id < 0` → some multi-cost_date (max 16 days). Multi-affid was 0 in this window even for negatives.
- **Decision:** keep `id > 0` filter (as in Combined). For positive ids, one user ≈ one affid ≈ one cost_date in recent data; `MIN(cost_date)` is defensive.
- **SQL:** `playbook/sql_steps/01_*.sql`, `01b_*.sql`, `01c_id_uniqueness_check_rp.sql`

## 2026-07-30 — Time & cost discipline

- **Decision:** All queries/scripts for this project should minimize BigQuery cost and runtime where possible, without sacrificing correctness or Excel-checkability.
- **Practice:** cheap step checks first (narrow dates / samples); full-history or multi-variant Colab runs only when needed.

## Inherited (not yet verified) — 2026-07-30

- Persistent trim mode (excluded users carry forward).
- RP organic share lookup capped at horizon 120 (App attribution change ~2025-08-12).
- Goal formula and constant organic share within a horizon — as coded in Combined.
- Trim defaults copied into `config/*.yaml` from Combined notebooks.
