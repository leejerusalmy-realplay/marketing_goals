*Lee Jerusalmy*

# Topic handoff — CV optimization

**Read after** main `playbook/HANDOFF.md`.  
**Opened:** 2026-08-11 — CV knob / cleanup optimization (not re-learn the pipeline).  
**Last updated:** 2026-08-13 — handoff to **next stage: `cv_oos_backtest`**.

---

## Next stage (start here)

**Question:** Does high CV (and the real cohort dispersion it reflects) make the Marketing Goal less reliable out of sample?

| | |
|--|--|
| **Code** | `experiments/cv_optimization/cv_oos_backtest/Marketing_Goals_Combined_RP_LS_Colab.ipynb` |
| **Spec** | `experiments/cv_optimization/cv_oos_backtest/GPT_SPEC_walkforward.md` |
| **Notes** | `experiments/cv_optimization/cv_oos_backtest/NOTES.md` |
| **Log** | `experiments/cv_optimization/EXPERIMENT_LOG.md` §6 |
| **Export** | `runs/<as_of>_rp_ls_cv_oos_backtest_<HHMMSS>/` |

**Do now**

1. Run / finish the OOS Colab (biweekly cutoffs, ~180d — slower than a single goals run).
2. Export CSVs under `runs/…_cv_oos_backtest_<ts>/` + add `LABEL.md`.
3. Update EXPERIMENT_LOG §6 Results + verdict; refresh README status row.
4. Especially interpret **`1→7`** vs mature patches, and whether CV ~20–30% predicts worse OOS error.

**Do not**

- Edit `reference/` or put experiment knobs into generic `notebooks/` until Lee locks.
- Treat MAD/IQR as a CV replacement (closed — keep CV).
- Re-run closed diagnostics unless Lee asks.

**Parallel (not blocking OOS)**

- **Winsor escalation** — Lee’s favorite closed trial so far (`cv_after > 0.15`: **11→8** capped). Still **park** for manager review before any production merge.
- Optional: Excel parity / reference spot-checks.

---

## What CV does (enough for this workstream)

Per **patch** (e.g. 1→7), each **cost_date** has:

`growth = ARPU_e / ARPU_s` (after winsor)

Then:

1. Weighted CV of those growths: **CV = σ_w / μ_w**, weight = **$ at patch start** (`sum_cum_s`).
2. Rank cost_dates by `|growth − unweighted mean|` (worst first).
3. Drop dates one-by-one until weighted CV ≤ **stop target**, or hit max removals.
4. Remaining dates feed day-steps + diagnostics (`n_cohort_dates_kept`, `flagged`, `mean_after`).

**Not CV:** day-step growth on the curve (that uses kept dates after this cleanup).  
**Not the same gate as** `min_cohort_dates` (RP 1 / LS 20 on **total** cost_dates in the patch window).

---

## Current knobs (production defaults — still in config)

| Knob | Role | RealPrize | LoneStar |
|------|------|-----------|----------|
| `cv_good_enough` | **Stop removing dates** when CV ≤ this | **0.10** | **0.10** |
| `cv_threshold` | **Flag** if final CV still > this | **0.15** | **0.175** |
| `max_remove_fraction` | Max share of cost_dates removable | **0.15** (~5 of 35) | same |
| Lookback | ~cost_dates per patch | **35** | **35** |
| Winsor in `TRIM_CONFIG` | Static floor per population | Web/Aff 1%; App/Blended 0% | Web/Blended 0%; Aff 1% |

Lee locked: date-removal target = **0.10 both brands**; brands differ on **flag** only.

When comparing CV trials, Lee prefers counting patches with **`cv_after > 0.15`** (unified), not only the production `flagged` column (LS 0.175).

---

## Closed / parked so far (do not re-open unless asked)

Full detail: `experiments/cv_optimization/EXPERIMENT_LOG.md` (**Experiments at a glance** + numbered sections).

| Trial | Result (short) | Verdict |
|-------|----------------|---------|
| **baseline** | `cv_after>0.15` = **11**/70; prod flagged **9**/70 | reference |
| **winsor_escalation** (capped) | `cv_after>0.15` **11→8**; prod flags 9→8 | **park** — Lee: best so far; manager |
| **winsor_escalation** (no cap) | prod flags 9→3 but early Web to 5% winsor | not preferred |
| **window_escalation** | 9→8 flags; not enough | **reject** |
| **union patches** | not implemented | **reject** |
| **robust_cv** | high CV often broad, not outlier-only | **reject** as CV replace |
| **cv_diagnosis** | drivers clarified | diagnostic-only |
| **dispersion_diagnostics** | high CV mostly real/central; keep CV | **closed** |
| **offline_2026-08-03** | early knob replays | park / context |

**Working theory:** High CV usually reflects real dispersion (not “SD from a few outliers”). Open gate is predictive value via OOS. Winsor is the only closed trial that meaningfully cut the CV>0.15 count — still not locked.

---

## Folder layout

Index: `experiments/cv_optimization/README.md` · run labels: `runs/README.md`

| Path | Role |
|------|------|
| `notebooks/Marketing_Goals_Combined_RP_LS*_` | **Generic** Combined (no experiment ladders) |
| `experiments/cv_optimization/cv_oos_backtest/` | **Current stage** — walk-forward OOS |
| `experiments/cv_optimization/winsor_escalation/` | Best closed trial so far (parked) |
| `experiments/cv_optimization/dispersion_diagnostics/` | Closed — keep CV |
| `experiments/cv_optimization/window_escalation/` | Reject |
| `experiments/cv_optimization/robust_cv/` | Reject as replace |
| `experiments/cv_optimization/cv_diagnosis/` | Diagnostic reference |
| `experiments/cv_optimization/baseline/` | Pointer to baseline run |
| `runs/2026-08-03_rp_ls_baseline/` | Baseline CSVs |
| `runs/2026-08-03_rp_ls_winsor_escalation_143601/` | Capped winsor (primary) |
| `runs/2026-08-03_rp_ls_dispersion_diagnostics_130742/` | Dispersion export |

**Language:** English only inside `marketing_goals/` files.

Do **not** edit `reference/`.

---

## Starter for the next chat

```
Continue marketing goals — CV optimization, next stage: cv_oos_backtest.
Read playbook/HANDOFF.md first, then playbook/handoffs/CV_OPTIMIZATION.md
and experiments/cv_optimization/EXPERIMENT_LOG.md (at a glance + §6).
Don’t re-teach the full pipeline. Don’t edit reference/.
Goal: finish walk-forward OOS — does high CV predict worse goal error?
Then update EXPERIMENT_LOG. Winsor escalation stays parked for manager (Lee’s best closed trial: CV>0.15 was 11→8).
```

---

*Update this file as decisions / experiments complete.*
