*Lee Jerusalmy*

# window_escalation

- **Code:** `Marketing_Goals_Combined_RP_LS_Colab.ipynb` in this folder.
- **Based on:** pre-winsor Combined Colab (no winsor-pct ladder).
- **Changes:**
  1. `AS_OF_DATE` pinned to `2026-08-03` (temporary).
  2. LoneStar `cv_threshold` 0.175 → **0.15** (notebook only).
  3. `LOOKBACK_ESCALATION_STEPS = [35, 45, 55, 65]` inside `patch_cv_adaptive`.
  4. SQL load floor uses `max(LOOKBACK_ESCALATION_STEPS)` so 65-day windows have data.
- **Export:** `combined_cv_summary_*_window_escalation_test.csv` under  
  `runs/<as_of>_rp_ls_window_escalation_<HHMMSS>/`
- **Not changed:** TRIM_CONFIG, winsor logic, `build_curve` lookback (still 35).
- **Status:** ready to run in Colab — then update the index README with flag counts.
