# Decisions (marketing goals) — RP + LS

Dated locks for this project. Newest first. Every lock notes which brand(s) it applies to.

*(Full pipeline Excel-lock still partial. Knobs mirror `config/realprize.yaml` + `config/lonestar.yaml` + notebook `BRAND_CONFIGS`.)*

## 2026-08-24 — Looker Goals view uses Combined v4 mapping; day cap 120

- **Brands:** RP + LS.
- **Decision:** `realplay_goals_performance` users SQL matches Combined v4 (app_affiliate, 2290, TikTok excludes, LS App floor, PPC/Organic in Blended only). Deposits `dsi ≥ 0`. Life days and patches stop at 120. Patch is a dimension, not a Parameter 1–5 value. Lee uploads the v4 goals table herself.
- **Where:** `marketing_context/dashboards/marketing_goals_120/`

## 2026-08-24 — Current Combined freeze is v4 (RP `app_affiliate` → Affiliate)

- **Brands:** RP only for the new rule. LS unchanged.
- **Decision:** Promote the RP `app_affiliate` experiment to Combined freeze **v4**. Folder: `notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/`. Matching export: `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`.
- **RP:** `channel_type = app_affiliate` → Affiliate (`non_app` / `acquired`). Remaining `APP` stays App.
- **LS:** same as v3 (`APP` and `cost_date >= 2026-08-05` → App).
- Rest of the engine is v3 (winsor_esc, LS App `native_early_rp_tail`, App organic off, `AS_OF_DATE` 2026-08-19).
- v3 stays archived. Generic `notebooks/` Combined stay the no-App baseline. Not a YAML lock.
- Working copy: `experiments/rp_app_affiliate_to_aff/`
- Topic: `playbook/handoffs/RP_APP_AFFILIATE.md`

## 2026-08-20 — Population from `marketing_population` (not hardcoded affid lists)

- **Brands:** RP + LS.
- **Decision:** Combined users SQL reads `marketing_population` on `*_cost_per_user` (same map as `analytics.stg_channel_affid_mapping`). Hardcoded Web / PPC / Organic affid lists are retired.
- **Label map (CMO → Goals):** `WEB` → Web, `APP` → App, `Google PPC` / `Bing PPC` / `PPC` → PPC, `Organic` → Organic, else Affiliate (Influencers, Test, Cost Adjustments, unmatched).
- **Exceptions:** `SEO` → Organic; `Shared Link` (affid 78) → Organic; **RP only** `affid = 2290` → Organic (map says Affiliate / internal yogev).
- **Still excluded:** TikTok WEB affids (RP `4313`; LS `4866`, `7127`) via `exclude_affids`.
- **LS App floor unchanged:** `marketing_population = 'APP'` counts as App only when `cost_date >= 2026-08-05`; earlier APP → Affiliate. v2 (no App) still maps APP → Affiliate.
- **Where:** v2 + v3 + v4 Colabs, `experiments/` working copies, `config/*.yaml`, `playbook/sql_steps/01*.sql`. Generic `notebooks/` Combined not updated.
- **v4 add-on (2026-08-24):** RP `channel_type = app_affiliate` → Affiliate. See decision above.

## 2026-08-19 — Current Combined freeze is v3 (replaced)

- **Brands:** RP + LS.
- **Decision:** Replace `notebooks/versions/v3_2026-08_winsor_esc_ls_app/` with the working LS App Colab. That folder is Lee’s **current Combined freeze**. Matching export: `runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/`.
- **In this freeze (still provisional vs generic Combined / YAML):**
  - LS App start `2026-08-05`; pre-floor `affid=1` → Affiliate
  - LS App `min_cohort_dates = 1`; Web / Aff / Blended stay 20
  - `native_early_rp_tail`; App winsor 0%; App organic off
  - CV concat keeps App rows only from the App pass (Blended once)
- Generic `notebooks/Marketing_Goals_Combined_RP_LS*.ipynb` stay the no-App baseline.
- Working copy: `experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`
- Topic: `playbook/handoffs/LS_APP.md`

## 2026-08-06 — Every playbook file dual-brand (RP + LS)

- Playbook docs rewrite: each file states **shared machinery** and **brand config differences**.
- Master knob side-by-side: `CONFIG_AND_KNOBS.md` / `METHODOLOGY.md`.
- Pipeline file: `PIPELINE_FLOW.md` (renamed from LS-only name).

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
