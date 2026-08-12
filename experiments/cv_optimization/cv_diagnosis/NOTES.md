*Lee Jerusalmy*

# cv_diagnosis

Exploratory only — explains **existing** Marketing Goals CV. Does not change methodology.

- **Code:** `Marketing_Goals_Combined_RP_LS_Colab.ipynb` in this folder  
  (built from generic Combined; `_build_notebook.py` can regenerate).
- **Does not touch:** `robust_cv/`, `window_escalation/`, `winsor_escalation/`, or generic `notebooks/`.
- **Same observations as production CV:** growth_ratio after winsor; weighted CV; date removal up to 15%.
- **AS_OF:** pinned `2026-08-03`.
- **Thresholds:** production (LS flag thr **0.175**, RP **0.15**) — not the unified-0.15 experiment.
- **Near-zero rules (documented in config cell):**
  - `NEAR_ZERO_GROWTH = 1e-6` on cohort growth_ratio
  - `NEAR_ZERO_USER_REV = 1e-6` on user cum revenue at patch end
- **Export folder:** `runs/<as_of>_rp_ls_cv_diagnosis_<HHMMSS>/`
  - `combined_cv_summary_cv_diagnosis.csv`
  - `cv_diagnosis_distributions.csv`
  - `cv_diagnosis_cohort_dates.csv`
  - `cv_diagnosis_final_high_cv.csv`
