*Lee Jerusalmy*

# Handoff — Marketing Goals (read this first in a new chat)

**Repo:** `lee_project/marketing_goals/`  
**Owner:** Lee Jerusalmy  
**Phase:** Learning / Excel-verify predecessor Combined logic. Rebuild into `src/` + `notebooks/` later — not yet.

---

## How to work with Lee on this project

1. Explain each calculation clearly (she is an analyst, not a developer).
2. Give small runnable SQL under `playbook/sql_steps/` → she checks in Excel before trusting the next step.
3. Prefer cheap/narrow BQ queries; heavy Colab only when needed.
4. Do **not** edit `reference/` (frozen predecessor notebooks).
5. Simple git: “save a version” / “push to main” / “go back to …” — no branches unless she asks.
6. Canonical memory: `lee_project/context/memory/` + this repo’s `playbook/`.

---

## Where the learning lives (start here)

| What | Where |
|------|--------|
| **Full LS pipeline (every chart box + Q&A)** | `playbook/LS_PIPELINE_FLOW.md` |
| **Same, readable Google Doc** | https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit |
| **Config cell / knobs map (RP+LS)** | `playbook/CONFIG_AND_KNOBS.md` |
| Short methodology | `playbook/METHODOLOGY.md` |
| Trim by pop (RP vs LS) + code paths | `playbook/TRIM_BY_POPULATION.md` |
| Numeric RP Web walkthrough | `playbook/WORKED_EXAMPLE_RP_WEB.md` |
| Brand knobs (YAML mirror) | `config/realprize.yaml`, `config/lonestar.yaml` |
| Excel-check SQL (steps 01–08) | `playbook/sql_steps/` + `README.md` |
| Frozen notebooks | `reference/Marketing_Goals_Combined_*.ipynb` |
| Project decisions | `playbook/DECISIONS.md` |
| Workspace prefs | `context/memory/preferences.md` § Marketing goals |

Lee’s flow chart (mental model):  
LS → population → cum/DSI → ARPU per patch → winsor → growth → CV → weighted day growth → ARPU D1 → curve → (+ organic share) → adjust? → Need extrapolation? → adjusted goal.

---

## What we already understand (do not re-teach from scratch)

- Cohort clock = **cost_date** (not dateReg); day D uses **dsi ≤ D−1**.
- Patches = maturity + winsor end-day + **CV on cost_dates**; curve shape = **day-to-day** weighted steps inside each patch.
- CV = **σ/μ** (weighted); stop at ≤ **0.10**; flag LS **> 0.175** / RP **> 0.15**; remove worst `|growth − unweighted mean|` first; max remove **15%**.
- Growth weight = **$ at patch start** (or day k−1 for day-steps). Day-1 anchor = **pooled $ / pooled users** (different weight).
- LS trim: Web/Blended **0%**, Aff **1%**; App not live. Cohort_trim not in Combined production. **Winsor does not drop users** — only caps $ (`min(cum,cap)`); N unchanged. Cap at patch end **e**, applied to s/e/day-steps.
- **min_cohort_dates:** RP = **1**, LS = **20** cost_dates — below gate → skip that patch.
- Organic share separate; goals use endpoint share; Web/Aff yes, Blended **forced 0**. LS organic scope today = **`all`** (no scope/bucket columns). Chart’s non_app/app = **RP** / future LS App.
- Final output = adjusted goals across horizons **7…365**, day-by-day — not monthly-only.
- RP organic cap at horizon **120**; **LS has no cap**.
- **Curve tail / `is_extrapolated`:** after stitch, if last real curve day &lt; 365, LS can fill forward with geometric mean of last **~30** day-to-day ARPU growth ratios; filled days = True. Goals still only `ARPU(day)/ARPU(horizon)×(1−org)`. Full write-up: `playbook/LS_PIPELINE_FLOW.md` → Box 11 → “Curve tail extrapolation”.
- Config lives in notebook `BRAND_CONFIGS` (+ YAML mirror); `apply_brand_globals` must run per brand so helpers see LS knobs not leftover RP globals.

---

## Excel verification status

| Topic | Status |
|-------|--------|
| Population / id>0 (RP) | Locked — see `playbook/DECISIONS.md` |
| dsi / cum / day indexing | SQL exists; largely understood |
| Patch growth, winsor, CV, stitch, organic | Explained; SQL through step **06** organic (RP-style); not all Excel-locked yet |
| Goal ratio (raw × organic → adjusted) | SQL step **07** ready (toy curve, free); Excel-lock pending |
| Curve tail / `is_extrapolated` | Documented in LS_PIPELINE_FLOW Box 11 + Google Doc |

---

## Rebuild: unified goals Colab (started 2026-08-05)

**Goal:** one end-to-end Colab → **one goals table** for **RP + LS**, **Blended + Web + Affiliate** (+ App on RP).

### Notebook

`notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` — **Colab** (auth + Drive + downloads).  
`notebooks/Marketing_Goals_Combined_RP_LS.ipynb` — Cursor / local twin (same pipeline).

**Agent ↔ notebook integration:** see `playbook/NOTEBOOK_INTEGRATION.md`  
(source on Drive = yes; live Colab session = no; put CSVs in `runs/` so the agent can review numbers).

### Locked output schema (main deliverable)

| Column | Notes |
|--------|--------|
| `brand` | `realprize` / `lonestar` |
| `population` | Web, Affiliate, App (RP), Blended |
| `goal_horizon` | 7…365 as in config |
| `day` | 1 … goal_horizon (life day; **not** rename to dsi) |
| `raw_goal_ratio` | ARPU(day) / ARPU(horizon) |
| `organic_share` | endpoint share; 0 for Blended |
| `adjusted_goal_ratio` | raw × (1 − organic); Blended = raw |

Optional / side: ARPU columns, `is_extrapolated`, `effective_patch` (in detail goals CSV); curve, organic, cv_summary (each with `brand`).

### Still open

- **Parity check** vs Combined RP/LS notebooks (spot-check a few populations × horizons).
- Excel-lock step 07 — not a blocker.
- Pure `src/` package can come after Colab parity is good.

---

## Sensible next steps (when Lee is ready)

1. **Primary:** open Colab, run unified notebook end-to-end, compare a few cells to Combined predecessors.
2. Optional: Excel-check step **07** when bandwidth allows.
3. Commit/push when she says “save a version”.

---

## Paste into a new agent chat (optional starter)

```
Continue marketing goals in lee_project/marketing_goals/.
Read playbook/HANDOFF.md first.
Unified Colab is notebooks/Marketing_Goals_Combined_RP_LS.ipynb.
Next: parity-check goals vs reference Combined notebooks (spot cells), then save a version.
Don’t edit reference/.
```
