*Lee Jerusalmy*

# SAMPLE outputs (illustrative)

**Brands:** production Combined exports include a **`brand`** column (`realprize` / `lonestar`) and both brands’ rows in one goals file under `runs/`.

**These SAMPLE_*.csv files** were drawn for **RealPrize column shape** as teaching examples. Numbers are **fake**, not a real run.

| SAMPLE file | Purpose |
|-------------|---------|
| `SAMPLE_realprize_combined_goals_adjusted.csv` | Main deliverable shape |
| `SAMPLE_realprize_combined_arpu_curve.csv` | Curve |
| `SAMPLE_realprize_combined_organic_share.csv` | Organic (RP has scope columns) |
| `SAMPLE_realprize_combined_cv_summary.csv` | CV flags |

For real dual-brand outputs, open `runs/2026-08-03_rp_ls_baseline/*.csv` and filter by `brand`.  
LS organic share is typically `scope=all` (no app/non_app split). Knobs: `CONFIG_AND_KNOBS.md`.
