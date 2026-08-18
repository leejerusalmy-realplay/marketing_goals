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
Notebooks: Marketing_Goals_Combined_RP_LS*.ipynb.
Don’t re-teach locked methodology. Don’t edit reference/.
```

**For LS App (as of 2026-08-18):**
```
Continue marketing goals — LS App bootstrap.
Read playbook/HANDOFF.md first, then playbook/handoffs/LS_APP.md
and experiments/ls_app_bootstrap/NOTES.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Don’t lock into generic notebooks/ or DECISIONS.md.
Lee’s current Combined freeze is v3 winsor_esc + LS App
(notebooks/versions/v3_2026-08_winsor_esc_ls_app/), not generic Combined.
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
| **Run notebooks** | `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` (+ local twin) |
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
- **min_cohort_dates:** RP **1**, LS **20** → else skip patch.
- Organic: endpoint share for whole horizon; Web/Aff/App yes; Blended **organic = 0**. RP scope app/non_app; LS **scope=all**. RP pin share at horizon **120**; LS no pin.
- Goals: `raw = ARPU(d)/ARPU(H)`, `adjusted = raw × (1 − organic)` (Blended = raw). Columns locked: brand, population, goal_horizon, day, raw_goal_ratio, organic_share, adjusted_goal_ratio.
- LS can **extrapolate curve tail** to 365 (`is_extrapolated`); RP does not.
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

- **Colab:** `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb`
- **Local twin:** `notebooks/Marketing_Goals_Combined_RP_LS.ipynb`
- **Sample run CSVs:** `runs/2026-08-03_rp_ls_baseline/`

Still open: parity vs `reference/` Combined spot-checks; Excel-lock 07; pure `src/` later.

---

## Status / next steps (update when session ends)

**As of 2026-08-18**

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
  - Generic `notebooks/` remain baseline.
- **v3 LS App freeze (2026-08-18):**
  - `notebooks/versions/v3_2026-08_winsor_esc_ls_app/`
  - v2 winsor_esc plus LS App (`native_early_rp_tail`). Provisional, not a lock.
- **LS App (2026-08-18) — next chat focus:** `playbook/handoffs/LS_APP.md`
  - Write-up: `experiments/ls_app_bootstrap/NOTES.md`
  - Colab (working copy): `experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`
  - Freeze: `notebooks/versions/v3_2026-08_winsor_esc_ls_app/`
  - Combined export: `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`
  - Method compare: `runs/2026-08-17_ls_app_bootstrap_114318/`
  - Provisional method: **`native_early_rp_tail`**. Winsor App 0% (no escalation). Organic **off**. Blended excludes App.
  - This Colab as_of still **2026-08-03** → splice day **14**. Not a copy of `2026-08-03_rp_ls_winsor_escalation_143601`.
  - Not locked. Do not edit generic Combined / `reference/` / `DECISIONS.md`.
  - **Open:** leftover `affid=1` (pre-2026-07-16) is inside App. Combined D1 is mixed; method-compare S=30 is leftover-heavy. Launch floor not applied.
- Pipeline learning solid. CV workstream parked — `playbook/handoffs/CV_OPTIMIZATION.md`.
- Generic Colab stays baseline. English only in `marketing_goals/` files.

**Sensible next (priority order)**

1. Continue from `playbook/handoffs/LS_APP.md`. First decision: floor LS App at launch **2026-07-16**?
2. Do not bump `AS_OF_DATE` alone. Do not run the `.py` unprompted.
3. App organic stays off until a mature App cohort exists.
4. July `first_day` winsor_esc improvement and CV OOS stay parked; lock nothing into generic/`DECISIONS.md` until Lee decides.

---

*When ending a long session: revise “Status / next steps” here so the next agent starts warm.*
