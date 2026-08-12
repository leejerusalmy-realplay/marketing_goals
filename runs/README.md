# runs/

Dated output of a goals run. **Never overwrite** — each export creates a new folder.

## Folder naming

```text
runs/<as_of_date>_<brand_slug>_<run_ts>/
runs/<as_of_date>_<brand_slug>_<experiment_tag>_<run_ts>/   ← CV / A-B trials
```

| Piece | Meaning | Example |
|-------|---------|---------|
| `as_of_date` | Cohort anchor from notebook (usually today − 2) | `2026-08-05` |
| `brand_slug` | Brands in this run: `rp`, `ls`, or `rp_ls` | `rp` |
| `experiment_tag` | Optional — CV trial name (e.g. `window_escalation`) | `window_escalation` |
| `run_ts` | Clock time of **export** (`HHMMSS`) so same-day re-runs stay separate | `143022` |

CV experiment notebooks and the variant index live under `experiments/cv_optimization/`.

Examples:
- First RP-only export today: `2026-08-05_rp_140512/`
- Second RP-only later today: `2026-08-05_rp_162230/`
- Full RP+LS: `2026-08-05_rp_ls_162245/`

Downloaded Colab CSVs use the same tag in the filename, e.g.
`combined_goals_2026-08-05_rp_140512.csv`.

## Files inside a run folder

| File | Role |
|------|------|
| `combined_goals.csv` | Main locked columns |
| `combined_goals_detail.csv` | + ARPU / patch flags |
| `combined_arpu_curve.csv` | Curves |
| `combined_organic_share.csv` | Organic |
| `combined_cv_summary.csv` | CV |
| `run_meta.csv` | as_of, brands, run_ts, exported_at |

## Which folder is "latest"?

Sort by folder name or by `run_meta.exported_at`. Say **"check the latest run"** in chat and the agent will pick the newest under `runs/`.
