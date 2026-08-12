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

**For CV optimization workstream (Lee’s next focus as of 2026-08-11):**
```
Continue marketing goals — CV optimization.
Read playbook/HANDOFF.md first, then playbook/handoffs/CV_OPTIMIZATION.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Goal: design and run a thoughtful process to optimize CV knobs (by brand), not recap methodology.
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
- **Sample run CSVs:** `runs/2026-08-03_rp_ls/`

Still open: parity vs `reference/` Combined spot-checks; Excel-lock 07; pure `src/` later.

---

## Status / next steps (update when session ends)

**As of 2026-08-12**

- Pipeline learning solid (including CV knobs, min_cohort_dates, curve stitch between patches).
- **CV optimization in progress** — log: `experiments/cv_optimization/EXPERIMENT_LOG.md`; handoff `playbook/handoffs/CV_OPTIMIZATION.md`; index `experiments/cv_optimization/README.md`.
- **Layout (Option B):** generic Combined stays in `notebooks/`; each CV trial is its own Colab under `experiments/cv_optimization/<variant>/`.
  - `winsor_escalation/` archived (flags 9→8 capped).
  - `window_escalation/` lookback ladder (LS thr 0.15).
  - `robust_cv/` / `cv_diagnosis/` — leave untouched if running / already exported.
  - `cv_oos_backtest/` **ready** — walk-forward: does high CV predict worse OOS goal error?
- Generic Colab stays **pre-winsor** baseline code (no experiment ladders).

**Sensible next (priority order)**

1. Run `experiments/cv_optimization/cv_oos_backtest/…Colab.ipynb` (biweekly cutoffs, ~180d — slower than a single goals run).
2. Update `experiments/cv_optimization/README.md` with CV↔OOS findings (especially 1→7 vs mature patches).
3. Only after a decision: merge into generic + `DECISIONS.md`; do not change thr from this notebook alone.
4. Optional parallel: Excel parity (08*), Colab vs `reference/` spot-checks.

---

*When ending a long session: revise “Status / next steps” here so the next agent starts warm.*
