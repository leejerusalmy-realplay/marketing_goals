# Decisions (marketing goals)

Dated locks for this project. Newest first.

*(None locked from Excel verification yet. Values below are inherited from predecessor Combined notebooks and live in `config/` until confirmed.)*

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
