*Lee Jerusalmy*

# winsor_escalation

- **Code:** `Marketing_Goals_Combined_RP_LS_Colab.ipynb` in this folder (archived from generic Colab after the 2026-08-11 test).
- **Idea:** escalate winsor pct toward brand `cv_threshold`; stop if revenue cut > 15% (absolute).
- **Runs:**
  - `runs/2026-08-03_rp_ls_winsor_escalation_nocap_133829/` — without revenue-cap columns (earlier export)
  - `runs/2026-08-03_rp_ls_winsor_escalation_143601/` — with `capped_by_revenue_limit` / `revenue_cut_fraction`
- **Compare write-up:** `cv_adaptive_vs_baseline_2026-08-12.md` (this folder)
- **Result (capped):** flags 9 → 8.
- **Status:** **park — needs manager review** (not rejected, not locked). See `../EXPERIMENT_LOG.md` §1.
