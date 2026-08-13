*Lee Jerusalmy*

# dispersion_diagnostics

Diagnostic only — shape of variability when existing CV is high. Does **not** replace CV.

- **Notebook:** `marketing_goals_dispersion_diagnostics.ipynb`  
  (built from generic Combined; `_build_notebook.py` can regenerate).
- **Does not touch:** `cv_oos_backtest/`, `cv_diagnosis/`, `robust_cv/`, or generic `notebooks/`.
- **Same observations as `cv_after`:** growth_ratio after winsor + existing date removal.
- **AS_OF:** pinned `2026-08-03`.
- **Thresholds:** production (LS flag thr **0.175**, RP **0.15**) — 15% is **not** applied to MAD/IQR/log metrics.
- **Key metrics:** `relative_mad_raw` (no ×1.4826), `scaled_mad_cv` (compare only), `relative_IQR`, P10–P90 spreads, `std_log`, within-patch ranks, `tail_sensitivity_signal`.
- **Export:** `runs/2026-08-03_rp_ls_dispersion_diagnostics_130742/`

## Verdict (2026-08-13 — Lee)

High CV is **mostly real / central**, not outlier-driven. Do **not** replace CV with MAD/IQR.

- Compared CV to MAD/Median, IQR/Median, P10–P90, and log dispersion on the same after-trim `growth_ratio`s.
- Most high-CV cases also have a wide center (e.g. LS Web `1→7`: P10≈1.60, P90≈3.54).
- “SD inflated by a few outliers → CV misleading” does **not** explain most of the problem.
- Exception: RP App `1→7` — center more concentrated; tails matter more.
- Log scale did not materially change the story.
- `1→7` remains a naturally high-variability patch; populations differ inside it.
- LS Web `180→270`: trimming removed extremes (~207% → ~19% CV) but residual dispersion stayed real.

**Remaining question:** does CV of ~20–30% (and the real spread it reflects) make the Marketing Goal less reliable? → `cv_oos_backtest`.
