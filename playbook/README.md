*Lee Jerusalmy*

# Playbook — RealPrize + LoneStar

How to understand and re-run marketing goals for **both brands** (shared pipeline; brand knobs differ).

---

## File roles (what each file is for)

### 1. Entry / agent transfer

| File | Purpose | When you open it |
|------|---------|------------------|
| **`HANDOFF.md`** | **Main handoff.** Status, what is locked, next step, working rules. | **Every new agent chat** — first |
| **`handoffs/`** | **Topic** handoffs (CV experiment, …). Do not replace the main handoff. | Only when working that topic |
| **`FOLDER_HYGIENE.md`** | Drive + git hygiene rules | Before creating new folders/files |

### 2. How it works (methodology)

| File | Purpose | Level |
|------|---------|--------|
| **`METHODOLOGY.md`** | What we compute + **shared vs different** RP vs LS (summary). | Short — first orientation |
| **`PIPELINE_FLOW.md`** | **Every pipeline step** (boxes): patch → winsor → CV → curve → organic → goals, with examples. | Full — “how it runs” |
| **`CONFIG_AND_KNOBS.md`** | **All knobs** (as_of, patches, trim_config, CV, min_cohort_dates, scope…). Where in code and yaml. | Knob map |
| **`TRIM_BY_POPULATION.md`** | Trim/winsor **by population** only (Web 1% vs 0%…). Cut from CONFIG. | Winsor cheat sheet |
| **`WORKED_EXAMPLE_RP_WEB.md`** | **Toy numeric example** (RP Web) for hand calculation. Not a real run. | When you want formulas in numbers |

### 3. Ops / history

| File | Purpose |
|------|---------|
| **`NOTEBOOK_INTEGRATION.md`** | How agent + you + Colab + `runs/` work together (not methodology). |
| **`DECISIONS.md`** | **Dated decision log** — what locked when. Not a pipeline explainer. |
| **`sql_steps/`** | Excel-check queries (usually RP fixtures; shared math). |
| **`examples/`** | Example CSVs (column shapes). |

### Google Doc
Plain-language twin (easier reading):  
https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit

---

## Why not one big file?

| Need | File |
|------|------|
| “What happens after a new agent starts?” | HANDOFF |
| “How is a numeric goal built?” | PIPELINE + WORKED_EXAMPLE |
| “What winsor % for Web on LS?” | CONFIG / TRIM |
| “What did we decide on 30.7?” | DECISIONS |
| “How do I share a run with the agent?” | NOTEBOOK_INTEGRATION |

The same knowledge appears briefly in a few places, with links to the full source — so orientation is not lost.

---

## Learning order

1. `HANDOFF.md`
2. `METHODOLOGY.md` or `CONFIG_AND_KNOBS.md` (shared vs different)
3. `PIPELINE_FLOW.md`
4. Optional: `WORKED_EXAMPLE_RP_WEB.md`
5. `sql_steps/` for Excel
6. `handoffs/<topic>.md` only for focused topics

## Verification rule

Explain → SQL in `sql_steps/` → Excel → only then lock.
