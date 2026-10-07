*Lee Jerusalmy*

# Handoff — Marketing Goals

**Read this first in every new agent chat.**  
Goal of this file: a new agent can pick up **without** re-deriving the pipeline or re-asking Lee the same methodology questions.

| | |
|--|--|
| **Repo** | `lee_project/marketing_goals/` (git: `leejerusalmy-realplay/marketing_goals`) |
| **Owner** | Lee Jerusalmy |
| **Phase** | Learning + Excel-verify + unified Combined Colab (RP + LS). Not a fully locked production package yet. |

---

## Agent-to-agent: how to hand off

1. New agent **opens this file first**, then links below for depth.
2. Does **not** re-teach locked bullets in “Already understand.”
3. Does **not** edit `reference/` (frozen predecessor notebooks).
4. Continues from **“Status / next steps”** at the bottom — update that section when the conversation ends or after a big lock.
5. Workspace prefs: `lee_project/context/memory/preferences.md` § Marketing goals.

### Paste into a new agent chat (starter)

**Default (general continue):**
```
Continue marketing goals in lee_project/marketing_goals/.
Read playbook/HANDOFF.md first (agent handoff).
Pipeline is RP + LS: playbook/PIPELINE_FLOW.md + CONFIG_AND_KNOBS.md.
Lee’s current Combined freeze is v5 (v4 mapping + staging deposit tables)
(notebooks/versions/v5_2026-10_stg_deposits_marketing/), not generic Combined.
Deposits: analytics.stg_realprize_casino_deposits_marketing and
analytics.stg_lonestar_casino_deposits_marketing (USD, no /100).
The 2026-10-02 export is still Astropay. Re-run before using v5 dollars.
Don’t re-teach locked methodology. Don’t edit reference/.
```

**For LS App (as of 2026-08-19):**
```
Continue marketing goals — LS App bootstrap.
Read playbook/HANDOFF.md first, then playbook/handoffs/LS_APP.md
and experiments/ls_app_bootstrap/NOTES.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Don’t copy into generic notebooks/ until Lee asks.
Lee’s current Combined freeze is v4 (includes LS App).
LS App method is unchanged from v3. See playbook/handoffs/LS_APP.md.
Matching v3 archive export: runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/
Current pack: notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/
Matching export: runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/
```

**For RP `app_affiliate` → Affiliate (as of 2026-08-24):**
```
Continue marketing goals — current Combined freeze is v4
(RP app_affiliate → Affiliate; LS mapping unchanged).
Read playbook/HANDOFF.md first, then playbook/handoffs/RP_APP_AFFILIATE.md
and experiments/rp_app_affiliate_to_aff/NOTES.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Don’t edit notebooks/versions/ (archives). Don’t apply the carve-out to LoneStar.
Don’t copy into generic notebooks/ until Lee asks.
Matching export: runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/
```

**For CV optimization — next stage `cv_oos_backtest` (as of 2026-08-13):**
```
Continue marketing goals — CV optimization, next stage: cv_oos_backtest.
Read playbook/HANDOFF.md first, then playbook/handoffs/CV_OPTIMIZATION.md
and experiments/cv_optimization/EXPERIMENT_LOG.md (at a glance + §6).
Don’t re-teach the full pipeline. Don’t edit reference/.
Goal: finish walk-forward OOS — does high CV predict worse goal error?
```

### Agent ↔ notebook loop (short)

| Thing | Agent can use? |
|--------|----------------|
| Notebook **code** in `notebooks/*.ipynb` | Yes (Drive) |
| CSVs in `runs/` | Yes after you export a run |
| Live Colab RAM | **No** — you run Colab; agent reads files |
| Live source of truth | Code on Drive + `runs/` + this handoff |

Detail (optional): `NOTEBOOK_INTEGRATION.md`.  
Topic-specific agent work goes under `playbook/handoffs/` — not a second main HANDOFF.

---

## How to work with Lee

1. Explain each calculation clearly (analyst, not developer).
2. Runnable SQL under `playbook/sql_steps/` → she checks in Excel before the next step.
3. Cheap/narrow BQ first; heavy Colab only when needed.
4. “Save a version” / “push to main” = commit + push when asked.
5. Every durable insight → playbook (and Google Doc when pipeline prose) + `DECISIONS.md` when locked.

---

## Where learning lives

| What | Where |
|------|--------|
| **This handoff (main)** | `playbook/HANDOFF.md` — always first |
| **Topic handoffs** | `playbook/handoffs/` (e.g. CV optimization) — only for that workstream |
| **Full pipeline (RP + LS, every box)** | `playbook/PIPELINE_FLOW.md` |
| **Shared vs brand knobs** | `playbook/CONFIG_AND_KNOBS.md`, `playbook/METHODOLOGY.md` |
| **Readable Doc** | https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit |
| **Trim by brand/pop** | `playbook/TRIM_BY_POPULATION.md` |
| **Toy numeric path (RP Web + LS knob compare)** | `playbook/WORKED_EXAMPLE_RP_WEB.md` |
| **Short methodology** | `playbook/METHODOLOGY.md` |
| **Dated locks** | `playbook/DECISIONS.md` |
| **Excel SQL** | `playbook/sql_steps/` |
| **Brand YAML** | `config/realprize.yaml`, `config/lonestar.yaml` |
| **Run notebooks** | **Current freeze:** `notebooks/versions/v5_2026-10_stg_deposits_marketing/` (working copy in `experiments/rp_app_affiliate_to_aff/`). Generic `notebooks/Marketing_Goals_Combined_RP_LS*.ipynb` = no-App baseline |
| **Frozen predecessors** | `reference/Marketing_Goals_Combined_*.ipynb` |

Shared flow chart:  
**brand** → population → cum/DSI → ARPU per patch → winsor → growth → CV → day growth steps → ARPU D1 → curve → organic share → adjust → [LS: tail extrapolate?] → adjusted goal.

---

## Already understand (do not re-teach)

- Cohort clock = **cost_date**; day **D** uses **dsi ≤ D−1**.
- Patches = maturity + winsor end-day + **CV on cost_dates**; curve shape = **day-to-day** weighted steps inside each patch.
- CV = **σ/μ** (weighted); stop ≤ **0.10**; flag **RP 0.15 / LS 0.175**; remove worst `|growth − unweighted mean|` first; max remove **15%**.
- Growth weight = **$ at patch start** (day-steps use prior-day $). Day-1 anchor = **pooled $ / pooled users**.
- Production trim = **winsor only**. Does **not** drop users — caps $ with `min(cum, cap)`. Cap from day **e**, applied to s/e/day-steps. Cohort_trim = labs only.
- Trim map: RP Web/Aff **1%**, RP App/Blended **0%**; LS Web/Blended **0%**, LS Aff **1%**.
- **min_cohort_dates:** RP **1**, LS Web/Aff/Blended **20** → else skip patch. **Current v4 freeze:** LS App **1** (temporary).
- Population from `cost_per_user.marketing_population` (WEB→Web, APP→App, PPC family→PPC, Organic→Organic, else Affiliate). Exceptions: SEO + Shared Link → Organic; RP `2290` → Organic. **v4:** RP `channel_type = app_affiliate` → Affiliate. TikTok WEB still excluded.
- Organic: endpoint share for whole horizon; Web/Aff/App yes; Blended **organic = 0**. RP scope app/non_app; generic LS Combined **scope=all**. **Current v4 freeze:** LS users SQL has RP-style scope/bucket; LS App organic forced **off**. RP pin share at horizon **120**; LS no pin.
- Goals: `raw = ARPU(d)/ARPU(H)`, `adjusted = raw × (1 − organic)` (Blended = raw). Columns locked: brand, population, goal_horizon, day, raw_goal_ratio, organic_share, adjusted_goal_ratio.
- LS App (v4, same as v3): `marketing_population = APP` and `cost_date >= 2026-08-05` → App; earlier APP → Affiliate. Native through last measured day, then RP App day-growth. App organic off.
- LS Web/Aff/Blended can **extrapolate curve tail** to 365 (`is_extrapolated`); RP does not. v4 LS App does **not** use LS tail fill.
- Config: notebook `BRAND_CONFIGS` (+ YAML mirror, not runtime-loaded). `apply_brand_globals` per brand.

---

## Excel verification status

| Topic | Status |
|-------|--------|
| Population / id>0 (RP) | Locked — `DECISIONS.md` |
| dsi / cum / day indexing | SQL exists; largely understood |
| Patch growth, winsor, CV, stitch, organic | Explained; SQL through **06** + **08** full patch parity; not all Excel-locked |
| Goal ratio | Step **07** toy SQL ready; Excel-lock pending |
| Curve tail (LS) | Documented in `PIPELINE_FLOW.md` Box 11 + Google Doc |

---

## Rebuild: unified Colab (RP + LS)

- **Current freeze (Lee, 2026-10-07):** `notebooks/versions/v5_2026-10_stg_deposits_marketing/`
- **Previous freeze (2026-08-24):** `notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/`
- **Working Colab:** `experiments/rp_app_affiliate_to_aff/Marketing_Goals_Combined_RP_LS_Colab_rp_app_affiliate_to_aff.ipynb`
- **Previous freeze (v3):** `notebooks/versions/v3_2026-08_winsor_esc_ls_app/`
- **Generic baseline (no LS App):** `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` + local twin
- **Sample generic run CSVs:** `runs/2026-08-03_rp_ls_baseline/`
- **Current freeze export:** `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`

Still open vs generic Combined: parity vs `reference/` spot-checks; Excel-lock 07; pure `src/` later.

---

## Status / next steps (update when session ends)

**As of 2026-10-07**

- **Current Combined freeze is v5:** `notebooks/versions/v5_2026-10_stg_deposits_marketing/`
  - Deposits: `analytics.stg_realprize_casino_deposits_marketing` and `analytics.stg_lonestar_casino_deposits_marketing`
  - Columns: `user_id`, `deposit_date`, `deposit_amount` (already USD), `deposit_status = 'APPROVED'`
  - User tables unchanged (`*_cost_per_user`)
  - Mapping unchanged from v4 (RP `app_affiliate` → Affiliate; LS App floor `2026-08-05`)
  - Working copy: `experiments/rp_app_affiliate_to_aff/`
  - `AS_OF_DATE` in that notebook is pinned **2026-10-02**
  - Export `runs/2026-10-02_rp_ls_rp_app_affiliate_to_aff_123941/` is still **Astropay**. Re-run Colab before treating goals as v5 dollars.
  - v4 stays archived. Not copied into generic `notebooks/`.

**As of 2026-08-24**

- **Current Combined freeze is v4:** `notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/`
  - RP: `channel_type = app_affiliate` → Affiliate; remaining APP stays App
  - LS mapping unchanged from v3
  - Matching export: `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`
  - Compared to last v3-mapping run `…105632/`: RP App H120 adj 0.794→0.715; RP Aff/Web 0.398→0.466; Blended almost flat
  - Working copy: `experiments/rp_app_affiliate_to_aff/`
  - Topic: `playbook/handoffs/RP_APP_AFFILIATE.md`
  - Not copied into generic `notebooks/` or YAML.
  - **Looker** `realplay_goals_performance` now uses this v4 user mapping (Lee uploading the v4 goals table separately).

**As of 2026-08-20**

- **Population mapping (Lee lock):** Combined v2 + v3 (and `experiments/ls_app_bootstrap/` Colabs) use `marketing_population` on `*_cost_per_user`, not hardcoded Web/PPC/Organic affid lists. Exceptions: SEO + Shared Link → Organic; RP `2290` → Organic. TikTok WEB still excluded. Generic `notebooks/` Combined still has the old affid lists until Lee asks.
- **Current Combined freeze** is still v3 code + export `…074309/` for the *run*. Re-run Colab before treating a new export as current — mapping change is in the notebooks, not yet a new `runs/` folder.

- **Current Combined freeze:** `notebooks/versions/v3_2026-08_winsor_esc_ls_app/` **replaced** with the working LS App Colab (same code as `experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`).
  - Matching export: `runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/`
  - App start **2026-08-05**; pre-floor `affid=1` → Affiliate; LS App `min_cohort_dates = 1`; Web/Aff/Blended stay 20
  - `native_early_rp_tail`; App winsor 0%; App organic off; splice after day **14**
  - CV export keeps App rows from the App pass only (LS Blended once)
  - `AS_OF_DATE` pinned **2026-08-19**
  - Provisional. Generic `notebooks/` stay no-App baseline. Not copied into YAML.
- **Old mixed App pack (keep):** `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/` — leftover `affid=1` inside App, no floor, as_of 2026-08-03. Do not treat as current.
- **April freeze (done):** Combined as of 2026-04-10 vs Apr 10–14 actuals.
  - Production: `runs/2026-04-10_rp_ls_goal120_realized_133457/`
  - Capped winsor_esc: `runs/2026-04-10_rp_ls_goal120_realized_winsor_esc_073346/`
  - Verdict: almost the same; only LS Web moved meaningfully (esc closer). Not a lock.
  - Ignore `runs/2026-08-14_rp_ls_132733/` (accidental generic Combined RUN).
- **July freeze (done):** same two engines, `AS_OF_DATE = 2026-07-10`, actuals through **2026-08-17**.
  - Code: `experiments/goal120_realized_2026-07-10/`
  - Production: `runs/2026-07-10_rp_ls_goal120_realized_064344/`
  - Capped winsor_esc: `runs/2026-07-10_rp_ls_goal120_realized_winsor_esc_064344/`
  - Day 120 is incomplete (max 39 life days), so **primary = shape so far** on a fixed cohort:
    `first_day` = 10 Jul users only, score `ARPU(d)/ARPU(39)` vs frozen `ARPU_nominal(d)/ARPU_nominal(39)`.
    `first_5_days` = 10–14 Jul users, same idea to day 35.
    `overall_level` = dollars only; do **not** use for shape.
  - Main comparison file: `compare_vs_production.csv` in the winsor folder.
  - **Verdict:** no big overall winner. On the main slice (`first_day`) winsor_esc is a **small improvement**:
    wins on LS Web, RP App, RP Web; ties on LS Aff, LS Blended, RP Aff, RP Blended; loses nowhere.
    On `first_5_days` the picture is mixed: production wins LS Web + RP App, winsor wins RP Web, rest ties.
    Bottom line: winsor helps a little in a few places, changes almost nothing elsewhere.
- **How Lee should read the July files:**
  - `compare_vs_production.csv` = engine vs engine; lower `shape_mae` wins.
  - `error_summary.csv` = one-engine scorecard by brand/pop/slice.
  - `compare_daily.csv` = full day-by-day path behind the plots.
  - Plot names: `first_day` = 10 Jul arrivals only; `first_5_days` = arrivals on 10–14 Jul.
- **Winsor notebook freeze (2026-08-18):**
  - Archived capped `winsor_escalation` Colab notebook under
    `notebooks/versions/v2_2026-08_winsor_escalation_combined/`.
- **LS App detail:** `playbook/handoffs/LS_APP.md` + `experiments/ls_app_bootstrap/NOTES.md`
  - Method compare: `runs/2026-08-17_ls_app_bootstrap_114318/`
  - Known: patch 7→14 is one App cost_date (5 Aug, 1,004 users). PART 2 Blended still copies all `users_df` (some App in Blended).
- Pipeline learning solid. CV workstream parked — `playbook/handoffs/CV_OPTIMIZATION.md`.
- English only in `marketing_goals/` files.

- **LookML Goals 120 dashboard (draft, 2026-08-20):** `lee_project/marketing_context/dashboards/marketing_goals_120/`. One explore, horizon 120, `cost_date` filter. Not deployed to Looker yet.

**Sensible next (priority order)**

1. Treat v5 code as the current Combined pack. The `…123941` export is still Astropay. Re-run Colab only when Lee asks, then that export becomes the v5 numbers.
2. App organic stays off until a mature App cohort exists.
3. Python twin `build_winsor_esc_plus_ls_app.py` still lags the Colab floor — do not run it for this freeze.
4. July `first_day` winsor_esc improvement and CV OOS stay parked. Do not copy into generic `notebooks/` until Lee asks.
5. Paste Goals 120 LookML into the Looker project when Lee is ready (`connection` must match the live UA model).

---

*When ending a long session: revise “Status / next steps” here so the next agent starts warm.*
