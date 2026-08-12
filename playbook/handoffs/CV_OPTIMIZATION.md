*Lee Jerusalmy*

# Topic handoff — CV optimization

**Read after** main `playbook/HANDOFF.md`.  
**Opened:** 2026-08-11 — CV knob / cleanup optimization (not re-learn the pipeline).  
**Last updated:** 2026-08-12 — experiment log filled (`experiments/cv_optimization/EXPERIMENT_LOG.md`). Current focus: `cv_oos_backtest`.

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

---

## Status 2026-08-11 — adaptive winsor test (in Colab only)

### Baseline (before this change)

From `runs/2026-08-03_rp_ls/combined_cv_summary.csv` (as_of **2026-08-03**):

- **70** patches, **9 flagged**.
- Pain concentrated in **early Web** (and RP App/Blended `1→7`). Affiliate / late patches mostly fine.
- **27/70** hit date-remove cap (5/35) without reaching `cv_good_enough=0.10`.
- Prior offline knob replays: `experiments/cv_optimization/offline_2026-08-03/` (early-max remove, greedy rank, etc.). Softest prior lever was `A_early_max25`; greedy/A25+B moved goals too much.

### What we implemented (test code — not locked in DECISIONS)

**File:** `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` only  
(local twin `Marketing_Goals_Combined_RP_LS.ipynb` **not** updated yet).

1. **`AS_OF_DATE` pinned** to `2026-08-03` so cohort windows match the baseline run.  
   Comment says **REVERT** to `now() - 2 days` after this test round / before production adoption.

2. **Per-patch winsor escalation** (inside `patch_cv_adaptive` only):
   - Ladder: `WINSOR_ESCALATION_STEPS = [0.0, 0.005, 0.01, 0.02, 0.03, 0.05]`
   - Start at population `TRIM_CONFIG` floor; only climb to steps ≥ floor.
   - For each candidate: winsor → date removal → `cv_after`.
   - Stop at **first** pct where `cv_after ≤ CV_THRESHOLD` (RP 0.15 / LS 0.175).
   - `get_trimmed_cohort_and_caps(..., pct_override=)` returns `trimmed, caps, method, pct_used`.
   - `cohort_trim` unchanged (no escalation).

3. **Revenue-cut cap** (addendum same day):
   - `MAX_REVENUE_CUT_FRACTION = 0.15`
   - At every candidate: `revenue_cut_fraction = 1 - (total_rev_after_trim / total_rev_before_trim)`
   - If cut **> 15%**: reject that pct, keep previous lower pct, set `capped_by_revenue_limit=True`.
   - Else if CV cleared → stop success.
   - Else if no more steps → keep best within revenue limit (may stay flagged).
   - Distinguishes: flagged because revenue stop vs flagged after exhausting safe steps.

4. **Diagnostics / export**
   - Stats + report columns: `floor_pct`, `pct_used`, `escalated`, `capped_by_revenue_limit`, `revenue_cut_fraction`, `n_escalation_steps_tried`
   - Print `>>> WINSOR ESCALATION REPORT` after flagged table
   - CSV names: `combined_cv_summary_{run_tag}_adaptive_test.csv` and Drive `combined_cv_summary_adaptive_test.csv` (do **not** overwrite baseline `combined_cv_summary.csv`)

### Known gap (important for tomorrow)

**Day-steps in `build_curve` still use config-floor winsor** (only unpack fix for 4-value return).  
Escalation affects CV date selection + `cv_summary` diagnostics; curve caps are **not** yet passed `pct_used`.  
If goals should reflect escalated winsor, next small change = pass `pct_used` into the second pass of `build_curve`.

### Do not silently lock

`TRIM_CONFIG` values unchanged. Production knobs not written to YAML / `DECISIONS.md` until Lee approves after comparing adaptive_test vs baseline.

---

## Comparison result (2026-08-12)

**Primary file:** `runs/2026-08-03_rp_ls_143601/combined_cv_summary_adaptive_test.csv` (has revenue-cap columns).  
**Earlier same day (no rev cap):** `runs/2026-08-03_rp_ls_133829/…`  
**Write-up:** `experiments/cv_optimization/winsor_escalation/cv_adaptive_vs_baseline_2026-08-12.md`

| | Baseline | + adaptive + abs 15% rev cap | adaptive, no rev cap |
|--|----------|------------------------------|----------------------|
| Flagged / 70 | 9 | **8** | **3** |
| Escalated | — | 7 | 9 |

- Only **RP Web 7→14** newly cleared under the capped run (`1%→2%`).
- Still flagged: RP Web 1→7 / 14→30 / 30→60; RP App 1→7; RP+LS Blended 1→7; LS Web 1→7 / 180→270.
- Absolute 15% $ cut **blocks** most useful climbs; without cap, 5% winsor on early Web (too aggressive).
- Affiliate floor 1% already cuts **25–49%** $ → `capped_by_revenue_limit=True` noise (CV already fine).
- **Goals/organic CSVs are not clean judges** of this test (RP App organic H=90 moved ~6pp; `build_curve` still on floor winsor).

**Verdict:** do **not** lock adaptive winsor yet — **parked for manager review** (Lee). Not a closed reject.

### Folder layout (Option B — 2026-08-12)

Index: `experiments/cv_optimization/README.md`

| Path | Role |
|------|------|
| `notebooks/Marketing_Goals_Combined_RP_LS*_` | **Generic** Combined (restored pre-winsor; no CV ladders) |
| `experiments/cv_optimization/winsor_escalation/` | Archived winsor-ladder Colab + prior runs |
| `experiments/cv_optimization/window_escalation/` | Lookback ladder + LS thr 0.15 |
| `experiments/cv_optimization/robust_cv/` | Robust CV side-by-side (LS thr 0.15) — **do not overwrite while running** |
| `experiments/cv_optimization/cv_diagnosis/` | Exploratory — why is CV high? |
| `experiments/cv_optimization/cv_oos_backtest/` | **Walk-forward** — does CV predict OOS goal error? |

### Sensible next (priority)

**Log:** `experiments/cv_optimization/EXPERIMENT_LOG.md` · GPT spec: `cv_oos_backtest/GPT_SPEC_walkforward.md`

1. **Run / finish** `cv_oos_backtest` → export → update EXPERIMENT_LOG Results.
2. **Dynamic winsor:** review with manager (parked — see EXPERIMENT_LOG §1).
3. Decide thresholds only after OOS evidence (+ manager call on winsor).
4. Do not merge into generic until Lee locks a decision.

---

## Where code lives

| Piece | Location |
|--------|----------|
| Experiment index | `experiments/cv_optimization/README.md` |
| Window-escalation Colab | `experiments/cv_optimization/window_escalation/` |
| Winsor-escalation Colab (archived) | `experiments/cv_optimization/winsor_escalation/` |
| Generic Combined (no CV ladders) | `notebooks/Marketing_Goals_Combined_RP_LS*_` |
| Baseline CV summary | `runs/2026-08-03_rp_ls/combined_cv_summary.csv` |
| Offline prior experiments | `experiments/cv_optimization/offline_2026-08-03/` |
| YAML mirror (unchanged) | `config/realprize.yaml`, `config/lonestar.yaml` |

Do **not** edit `reference/`.

---

## Starter for the next chat

```
Continue marketing goals — CV optimization.
Read playbook/HANDOFF.md first, then playbook/handoffs/CV_OPTIMIZATION.md
and experiments/cv_optimization/README.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Next: finish cv_oos_backtest; update EXPERIMENT_LOG; winsor escalation parked for manager.
```

---

*Update this file as decisions / experiments complete.*
