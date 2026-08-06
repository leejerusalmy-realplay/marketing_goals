*Lee Jerusalmy*

# Working with the agent — notebooks (RP + LS)

How Cursor and Lee share one notebook loop (code → run → outputs → edits → git).

**Brands:** the Combined notebook runs **both** RealPrize and LoneStar (`RUN_BRANDS`). Each brand uses its own `BRAND_CONFIGS` knobs (winsor, CV flag, min_cohort_dates, scope…). See `CONFIG_AND_KNOBS.md`.

---

## What is connected

| Thing | Connected to agent? | How |
|--------|---------------------|-----|
| Notebook **source** in `notebooks/*.ipynb` | **Yes** | Drive under `lee_project/` |
| **CSV outputs** under `runs/` | **Yes** after export | Goals include `brand` = realprize / lonestar |
| **Cell outputs** in the `.ipynb` | Only if saved | Save so Drive syncs |
| Live Colab RAM | **No** | You run; agent reads files |

---

## One source of truth

| Role | File |
|------|------|
| Edit with agent | Either twin (mirror logic in both) |
| Run Colab | `Marketing_Goals_Combined_RP_LS_Colab.ipynb` |
| Run Cursor | `Marketing_Goals_Combined_RP_LS.ipynb` |
| Numbers | `runs/<as_of>_*` CSVs — filter by `brand` |

Set `RUN_BRANDS = ['realprize']` or `['lonestar']` for a single-brand debug run.

---

## Loop

1. You run end-to-end (`MONITOR_STEPS = True`). Both brands unless you narrowed `RUN_BRANDS`.
2. Export CSVs into `marketing_goals/runs/…`.
3. In chat: e.g. “RP Web D120 organic looks wrong” or “LS Aff winsor…”
4. Agent reads `runs/` (+ notebook if saved), edits code, updates playbook.
5. You re-run; “save a version” → commit when asked.

Brand-specific bugs almost always mean knobs: `apply_brand_globals`, trim_config, CV threshold, scope, min_cohort_dates — not a different pipeline.

---

## Colab tips

1. Use the **Drive** copy of the Colab notebook.
2. Mount Drive / export under `lee_project/marketing_goals/runs/`.
3. Reload tab if the agent edited the file while Colab was open.
4. Folder tags look like `2026-08-05_rp_ls_<HHMMSS>` when both brands ran.

---

## Cursor tips

1. Python 3.9+ + `pandas-gbq` as needed.
2. Export `runs/` is the canonical review surface (filter `brand`).

---

## Git

Repo: `https://github.com/leejerusalmy-realplay/marketing_goals` · branch `main`  
Phrases: “save a version” / “push to main” / “go back to …”
