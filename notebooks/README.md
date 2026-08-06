# notebooks/

Colab-friendly notebooks for producing goals.

## Current (v1)

| File | Role |
|------|------|
| **`Marketing_Goals_Combined_RP_LS_Colab.ipynb`** | **Use this in Google Colab** (auth + Drive + downloads) |
| **`Marketing_Goals_Combined_RP_LS.ipynb`** | Cursor / local (service-account JSON) — same logic |

**Agent collaboration** (see outputs, edit cells, git versions): `../playbook/NOTEBOOK_INTEGRATION.md`

### How to run (Colab)

Use **`Marketing_Goals_Combined_RP_LS_Colab.ipynb`**.

1. Upload to Colab or open from Drive → Runtime → Run all.
2. Allow Google auth; optionally mount Drive in the Drive cell.
3. Run top → bottom (auth → optional Drive → config → helpers → load + build → export).
3. Main download: `combined_goals_<as_of>_rp_ls.csv` with locked columns:

   `brand`, `population`, `goal_horizon`, `day`, `raw_goal_ratio`, `organic_share`, `adjusted_goal_ratio`

4. Side files (parity / debug): detail goals (ARPU + patch flags), ARPU curve, organic share, CV summary.
5. If Drive is mounted at `lee_project/marketing_goals/runs/`, the export cell also writes `runs/<as_of>_rp_ls/`.

### Brand knobs

Config is in the notebook config cell (mirrors `../config/realprize.yaml` + `../config/lonestar.yaml`):

- RP: Web / App / Affiliate, CV 0.15, organic cap 120, no tail extrapolation
- LS: Web / Affiliate, CV 0.175, min 20 cohort dates, tail extrapolation on, no organic cap

### Source

Logic ported from `../reference/Marketing_Goals_Combined_*.ipynb` (do not edit reference/).  
Curve builder uses the LS two-pass + optional tail form; RP runs with `extrapolate_tail=False`.

Until parity vs Combined is checked cell-by-cell, treat numbers as draft.

### Cursor / local (same notebook)

1. Install packages once:
   ```bash
   pip install pandas numpy pandas-gbq google-cloud-bigquery pyarrow
   ```
2. Open `Marketing_Goals_Combined_RP_LS.ipynb` in Cursor.
3. Run cells top → bottom (auth auto-picks the lee_project BQ JSON).
4. Outputs → `../runs/<as_of_date>_rp_ls/`.

First run is heavy (full history floor for both brands). Keep `MONITOR_STEPS = True` to watch tables appear under each part.

Optional: run only one brand first by setting in the config cell  
`RUN_BRANDS = ['realprize']`  (or `['lonestar']`).
