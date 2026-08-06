# Working with the agent on marketing goals notebooks

*Lee Jerusalmy*

How Cursor and Lee share one notebook loop (code → run → outputs → edits → git).

---

## What is connected

| Thing | Connected to agent? | How |
|--------|---------------------|-----|
| Notebook **source** (cells / code) in `notebooks/*.ipynb` | **Yes** | On Google Drive under `lee_project/` — agent can read & edit |
| **CSV outputs** under `runs/` | **Yes** after a run saves them | Agent reads CSVs, compares, diffs |
| **Cell outputs** inside the `.ipynb` | **Yes only if saved into the file** | Run in Cursor **or** Colab → **File → Save** so Drive syncs |
| Live Colab runtime (RAM, mid-run state) | **No** | Agent is not inside Colab’s session |

So: full integration = **file on Drive + `runs/` + git**, not a live remote desktop into Colab.

---

## One source of truth (pick this)

| Role | File |
|------|------|
| Edit in Cursor / agent | Either twin (keep them in sync when we change logic) |
| Run in Colab | `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` |
| Run in Cursor | `notebooks/Marketing_Goals_Combined_RP_LS.ipynb` |
| Numbers to review | `runs/<as_of_date>_rp_ls/*.csv` |

When the agent changes pipeline logic, ask to **mirror both notebooks** (or say “Colab only”).

---

## Loop that works with the agent

1. **You run** (Colab or Cursor) end-to-end with `MONITOR_STEPS = True`.
2. **You save outputs**
   - Prefer export into `marketing_goals/runs/<date>_rp_ls/` (Drive mount in Colab, or automatic path locally).
   - Optional: **Save** the notebook so printed cell outputs land in the `.ipynb`.
3. **You say in chat** e.g.  
   - “look at the latest run”  
   - “Part 3 organic share looks wrong on RP Web D120”  
   - “change CV threshold…”  
4. **Agent** opens `runs/` (+ notebook if outputs saved), proposes/edits code, updates playbook if needed.
5. **You re-run** only what changed (or full refresh).
6. **You say “save a version”** → agent commits + pushes `marketing_goals` git (when you ask).

---

## So the agent can *see* a run

Minimum (best for cost/clarity): CSVs in `runs/`  
Optional: saved notebook with execution outputs under each cell  

Not enough alone: screenshots, or a Colab tab that never saved.

---

## Colab tips for integration

1. Open the **Drive** copy of `…_Colab.ipynb` (not a one-off upload that never writes back).
2. After a run: mount Drive (export cell) **and/or** download CSVs into `lee_project/marketing_goals/runs/`.
3. If the agent edited the notebook while Colab was open: **reload** the tab from Drive before the next edit, or paste changes risk overwriting.
4. Say **“save a version”** after a stable checkpoint you trust.

---

## Cursor tips

1. Kernel: **Python 3.9** (`/usr/bin/python3`) + `pip install --user pandas-gbq` once.
2. Run cells here → outputs often embed in the notebook file → agent can open the same file and read them.
3. Export still writes `runs/` — treat that as the canonical goals table.

---

## Git (same as rest of this repo)

Repo: `https://github.com/leejerusalmy-realplay/marketing_goals`  
Branch: `main`  
Phrase: **“save a version”** / **“push to main”** / **“go back to …”**

Notebooks are not gitignored — code + structure get versioned. Prefer **not** committing huge embedded outputs if the file balloons; `runs/` CSVs are the intentional artifact.


---

## Run output naming (same day safe)

Each export uses a unique tag:

`<as_of_date>_<brand_slug>_<HHMMSS>`

- Folder: `runs/2026-08-05_rp_143022/`
- Files: `combined_goals_2026-08-05_rp_143022.csv`, …

Re-running export later today creates **another** folder/file set; nothing is overwritten.
