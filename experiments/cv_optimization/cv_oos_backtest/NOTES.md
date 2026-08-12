*Lee Jerusalmy*

# cv_oos_backtest

Walk-forward test: **does in-sample CV predict out-of-sample goal error?**

- **Code:** `Marketing_Goals_Combined_RP_LS_Colab.ipynb` (regenerate via `_build_notebook.py`)
- **GPT spec:** `GPT_SPEC_walkforward.md`
- **Log entry:** `../EXPERIMENT_LOG.md` §6
- **Does not touch:** `robust_cv/`, `cv_diagnosis/`, other variants, or generic `notebooks/`
- **Does not change:** CV math, trim, lookback 35, thresholds, goal formulas

## Goal definition (framework)

For each brand × population × patch at historical cutoff `T`:

`goal = mean_after` from existing `patch_cv_adaptive`

= weighted mean of kept cohort `growth_ratio = ARPU_e / ARPU_s`

This is the quantity existing CV summarizes. Full day-level curves / organic shares are out of scope in this notebook.

## Walk-forward / no look-ahead

At cutoff `T`:

1. Training window = exact production window via `patch_cv_adaptive(as_of_date=T)` (35 cohorts ending `T − e`).
2. Freeze `goal` + `cv_after`.
3. Test = next 7 / 14 / 30 **cost_dates after training_end** that are mature by pinned `EVAL_AS_OF` (`AS_OF_DATE = 2026-08-03`).
4. Actuals = single-date growth with the same winsor helper (documented: winsor on that date only — does not borrow other dates).

If fewer than H mature future dates exist → `insufficient_test_data=True` (no artificial fill).

## Knobs (framework only)

| Knob | Default |
|------|---------|
| `TEST_HORIZONS` | 7, 14, 30 |
| `PRIMARY_TEST_HORIZON` | 14 |
| `CUTOFF_FREQ_DAYS` | 14 (biweekly; weekly = slower) |
| `CUTOFF_SPAN_DAYS` | 180 |
| LS `cv_threshold` | **0.175** (production) |

## Export

`runs/<as_of>_rp_ls_cv_oos_backtest_<HHMMSS>/`
