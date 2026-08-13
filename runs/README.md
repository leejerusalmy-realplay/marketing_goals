# runs/

Dated output of a goals run. **Never overwrite** — each export creates a new folder.

## CV experiment runs (as_of 2026-08-03) — short labels

| Short label | Folder | What it is |
|-------------|--------|------------|
| **Baseline / reference** | `2026-08-03_rp_ls_baseline/` | Production Combined — comparison point (9/70 flagged) |
| **Winsor escalation + $ cap** | `2026-08-03_rp_ls_winsor_escalation_143601/` | Winsor ladder with 15% revenue-cut cap |
| **Winsor escalation no cap** | `2026-08-03_rp_ls_winsor_escalation_nocap_133829/` | Same trial, no revenue cap (earlier same day) |
| **Window escalation** | `2026-08-03_rp_ls_window_escalation_080607/` | Lookback 35→65 |
| **Robust CV (MAD)** | `2026-08-03_rp_ls_robust_cv_111132/` | CV vs MAD×1.4826 |
| **CV diagnosis** | `2026-08-03_rp_ls_cv_diagnosis_114014/` | Why CV is high (zeros / whales / trends) |
| **Median/Quantile dispersion** | `2026-08-03_rp_ls_dispersion_diagnostics_130742/` | Tails vs center / log |

Index + verdicts: `experiments/cv_optimization/EXPERIMENT_LOG.md`.

## Folder naming

```text
runs/<as_of_date>_<brand_slug>_<run_ts>/
runs/<as_of_date>_<brand_slug>_<experiment_tag>_<run_ts>/   ← CV / A-B trials
```

| Piece | Meaning | Example |
|-------|---------|---------|
| `as_of_date` | Cohort anchor from notebook (usually today − 2) | `2026-08-05` |
| `brand_slug` | Brands in this run: `rp`, `ls`, or `rp_ls` | `rp` |
| `experiment_tag` | Optional — short experiment name | `dispersion_diagnostics` |
| `run_ts` | Clock time of **export** (`HHMMSS`) so same-day re-runs stay separate | `143022` |

Prefer an `experiment_tag` in the folder name (not bare `_HHMMSS`) so Drive stays readable.

## Files inside a run folder

| File | Role |
|------|------|
| `combined_goals.csv` | Main locked columns |
| `combined_goals_detail.csv` | + ARPU / patch flags |
| `combined_arpu_curve.csv` | Curves |
| `combined_organic_share.csv` | Organic |
| `combined_cv_summary*.csv` | CV (name may include experiment suffix) |
| `run_meta.csv` | as_of, brands, run_ts, exported_at |
| `LABEL.md` | One-line human label (optional) |

## Which folder is "latest"?

Sort by folder name or by `run_meta.exported_at`. Say **"check the latest run"** in chat and the agent will pick the newest under `runs/`.
