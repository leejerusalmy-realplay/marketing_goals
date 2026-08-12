*Lee Jerusalmy*

# robust_cv

- **Code:** `Marketing_Goals_Combined_RP_LS_Colab.ipynb` in this folder.
- **Based on:** generic Combined Colab (no winsor ladder, no window ladder).
- **Keeps:** existing CV, date removal, trim/winsor, flagged rule, goals.
- **Adds:** Robust CV = `1.4826 × MAD / median` on the same `growth_ratio` rows used for `cv_before` / `cv_after`.
- **Also for this test:** LS `cv_threshold` → **0.15** (unified with RP); `AS_OF_DATE` pinned to **2026-08-03**.
- **Diagnosis (relative, retunable constants):**
  - `OUTLIER_DRIVEN` if `robust_cv_after / cv_after <= 0.70`
  - `CONSISTENT_VARIABILITY` if ratio in `(0.70, 1.15]`
  - `REVIEW` otherwise / missing
- **Export:** `runs/<as_of>_rp_ls_robust_cv_<HHMMSS>/`
  - `combined_cv_summary_robust_cv_test.csv`
  - `combined_cv_robust_compare.csv`
- **Status:** ready to run — then update the index README with findings.
