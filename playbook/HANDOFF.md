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
| Short methodology | `playbook/METHODOLOGY.md` |
| Trim by pop (RP vs LS) | `playbook/TRIM_BY_POPULATION.md` |
| Numeric RP Web walkthrough | `playbook/WORKED_EXAMPLE_RP_WEB.md` |
| Brand knobs | `config/realprize.yaml`, `config/lonestar.yaml` |
| Excel-check SQL (steps 01–06) | `playbook/sql_steps/` + `README.md` |
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
- LS trim: Web/Blended **0%**, Aff **1%**; App not live. Cohort_trim not in Combined production.
- Organic share separate; goals use endpoint share; Web/Aff yes, Blended **forced 0**. LS organic scope today = **`all`** (chart’s non_app/app = RP / future App).
- Final output = adjusted goals across horizons **7…365**, day-by-day — not monthly-only.
- RP organic cap at horizon **120**; **LS has no cap**.
- **Curve tail / `is_extrapolated`:** after stitch, if last real curve day &lt; 365, LS can fill forward with geometric mean of last **~30** day-to-day ARPU growth ratios; filled days = True. Goals still only `ARPU(day)/ARPU(horizon)×(1−org)`. Full write-up: `playbook/LS_PIPELINE_FLOW.md` → Box 11 → “Curve tail extrapolation”.

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

## Tomorrow: rebuild unified goals script (kickoff)

**Goal:** one end-to-end script → **one goals table** for **RP + LS**, **Blended + Web + Affiliate** (+ App on RP when live).

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

Optional later/detail: ARPU_$ columns, `is_extrapolated`, `effective_patch`, `as_of_date`, `run_id`. Side files OK: curve, organic, cv_summary (each with `brand`).

### Implementation plan (when coding starts)

1. **Engine: Google Colab notebook first** (not a pure local `src/` CLI as the v1 entrypoint).  
   Port logic into `notebooks/` (or Colab-friendly script cells) using `config/realprize.yaml` + `config/lonestar.yaml`.
2. **Structure = predecessor Combined** as the starting shape  
   (same pipeline sections / exports spirit as `reference/Marketing_Goals_Combined_*.ipynb`), then unify RP + LS into one run and one goals table with the locked columns + `brand`.
3. Parity checks vs Combined on a few cells after first runnable draft.
4. Write dated outputs under `runs/` (downloadable from Colab too).

### Still open (not blockers to start coding)

- Excel-lock step 07 — Lee **has not** done the Excel check yet (formula understood; lock later).
- Detail columns in v1 vs main-only (default for Colab Combined-like start: keep Combined-style extras if they already exist in the predecessor export; main locked columns must be present).
- Pure `src/` package can come after Colab works.

---

## Sensible next steps (when Lee is ready)

1. **Tomorrow primary:** start unified goals **Colab notebook** on Combined structure (see above).
2. Optional later: Excel-check step **07** when Lee has bandwidth.
3. Commit/push when she says “save a version”.

---

## Paste into a new agent chat (optional starter)

```
Continue marketing goals in lee_project/marketing_goals/.
Read playbook/HANDOFF.md first (section Tomorrow rebuild), then playbook/DECISIONS.md (2026-08-04 Colab).
Start the unified RP+LS goals Colab notebook from Combined structure.
Main columns: brand, population, goal_horizon, day, raw_goal_ratio, organic_share, adjusted_goal_ratio.
Don’t edit reference/.
```
