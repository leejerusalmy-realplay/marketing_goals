*Lee Jerusalmy*

# CV optimization — experiment log

Living log of what we tried, what the numbers said, and why we kept / rejected / parked each idea.  
**Not** production locks — those go in `playbook/DECISIONS.md` only when Lee approves.

Folder / notebook index: `README.md` in this folder.  
Topic handoff: `playbook/handoffs/CV_OPTIMIZATION.md`.  
CSV exports: `marketing_goals/runs/` (each run has a `LABEL.md`).

---

## Experiments at a glance

Plain-language map of every folder under `experiments/cv_optimization/`.  
Details, numbers, and rationale are in the numbered sections below.

| Folder | In one sentence | Question it answers | Verdict |
|--------|-----------------|---------------------|---------|
| **`baseline/`** | Pointer to the frozen production comparison run (not a code change). | What do flags look like with current knobs? | **reference** |
| **`winsor_escalation/`** | Raise winsor % per patch until CV clears (optional 15% revenue-cut stop). | Can stronger trimming clear high-CV flags safely? | **park** (manager) |
| **`window_escalation/`** | If still flagged, grow lookback 35→45→55→65 and retry. | Does a longer history stabilize early patches? | **reject** |
| **`robust_cv/`** | Side-by-side: existing CV vs `1.4826 × MAD / median`. | Is high CV mostly a few outliers MAD would ignore? | **reject** as CV replace |
| **`cv_diagnosis/`** | Broader forensics: zeros, whales, skew, trends, sample size. | *Why* is CV high on these patches? | **diagnostic-only** |
| **`dispersion_diagnostics/`** | MAD/IQR/P10–P90/log on the same after-trim growth ratios (no 15% pass/fail on new metrics). | When CV is high: tails, broad center, or multiplicative shape? | **closed** — keep CV |
| **`cv_oos_backtest/`** | Walk-forward: freeze goal + CV at historical T; score later cohort dates. | Does high CV mean a less reliable Marketing Goal out of sample? | **open** (main next) |
| **`offline_2026-08-03/`** | Early Python knob replays (not Colab); e.g. early-patch max-remove. | Pre–Option B scratch — context only. | **park** |

Also discarded early (no folder): **union patches** — GPT merge idea; **reject**.

**How to read this log:** start with the table above → open the matching numbered section for results → use `runs/…` paths for CSVs.

---

## How to read verdicts

| Verdict | Meaning |
|---------|---------|
| **reject** | Do not adopt into production methodology |
| **park** | Interesting / incomplete; not adopted; may revisit |
| **diagnostic-only** | Explains the data; does not change the model |
| **open** | Running or awaiting results / Lee decision |
| **reference** | Frozen comparison baseline |
| **closed** | Finished diagnostic; conclusion recorded; no methodology change |

---

## Baseline (reference)

| | |
|--|--|
| **Idea** | Production Combined knobs as of sample run |
| **Code** | `notebooks/Marketing_Goals_Combined_RP_LS*_` (generic) |
| **Run** | `runs/2026-08-03_rp_ls_baseline/` |
| **as_of** | 2026-08-03 |
| **Result** | **9 / 70** patches flagged (existing CV logic; LS thr 0.175) |
| **Verdict** | **reference** |
| **Why** | Comparison point for all CV trials |

Pain concentrated in early Web / early Blended / RP App `1→7`; many patches hit date-remove cap without reaching `cv_good_enough=0.10`.

---

## 1. Dynamic winsor (`winsor_escalation`)

| | |
|--|--|
| **Idea** | Escalate winsor % per patch toward brand `cv_threshold`; optional absolute 15% revenue-cut stop |
| **Code** | `experiments/cv_optimization/winsor_escalation/` |
| **Runs** | `runs/2026-08-03_rp_ls_winsor_escalation_nocap_133829/` · `…_winsor_escalation_143601/` (with revenue cap) |
| **Write-up** | `experiments/cv_optimization/winsor_escalation/cv_adaptive_vs_baseline_2026-08-12.md` |
| **Result** | With abs 15% $ cut: patches with **`cv_after > 0.15`:** **11 → 8** (cleared RP Web `7→14`, LS Web `14→30`, LS Web `30→60`). Production `flagged` column (LS thr 0.175): **9 → 8**. Without cap: production flags **9 → 3** but early Web climbs to **5%** winsor; still **8** patches with CV>0.15. Affiliate floor 1% already cuts 25–49% $ → noisy “capped” flags. |
| **Verdict** | **park — needs manager review** (not rejected; not locked). **Lee (2026-08-13): most successful trial so far** on the CV>0.15 count (11→8). |
| **Why / open question** | Best flag reduction among closed trials under a unified 0.15 lens; still does not clear the hard early-Web / `1→7` cases. Uncapped clears more production flags but early Web climbs to 5% winsor. Affiliate floor already cuts large $ share. Curve still on floor winsor (`pct_used` not wired). **Lee: decide with manager** whether to pursue (e.g. incremental cut-above-floor) or drop. |

---

## 2. Dynamic windows (`window_escalation`)

| | |
|--|--|
| **Idea** | If still flagged after date removal, grow lookback `35 → 45 → 55 → 65` and retry; LS thr unified to 0.15 for the test |
| **Code** | `experiments/cv_optimization/window_escalation/` |
| **Run** | `runs/2026-08-03_rp_ls_window_escalation_080607/` |
| **Result** | Flags **9 → 8**; **11** patches used lookback &gt; 35. Lee: **not good** enough as a fix. |
| **Verdict** | **reject** |
| **Why** | Window growth did not meaningfully solve early-patch CV pain; adds complexity / maturity lag without clear win. |

---

## 3. Union patches

| | |
|--|--|
| **Idea** | GPT suggestion to union / merge patches (details not implemented in repo) |
| **Code / run** | none kept |
| **Verdict** | **reject** (discarded early) |
| **Why** | Lee: GPT proposed; not useful — skip. No further tracking. |

---

## 4. MAD / Robust CV (`robust_cv`)

| | |
|--|--|
| **Idea** | Keep existing CV; add Robust CV = `1.4826 × MAD / median` on same `growth_ratio`s; classify OUTLIER_DRIVEN vs CONSISTENT_VARIABILITY (ratio rules). LS thr 0.15 for this test only. |
| **Code** | `experiments/cv_optimization/robust_cv/` |
| **Run** | `runs/2026-08-03_rp_ls_robust_cv_111132/` |
| **Result** | Among flagged: mostly **CONSISTENT_VARIABILITY** (9), not OUTLIER_DRIVEN (0 in flagged set from that export’s diagnosis counts — overall OUTLIER_DRIVEN existed on non-flagged). High CV is often **broad dispersion**, not a few outliers MAD would dismiss. |
| **Verdict** | **reject as CV replacement** · **diagnostic-only** (useful side metric, not production flag) |
| **Why** | Does not justify replacing σ/μ CV. Led to deeper diagnosis + OOS question instead. |

---

## 5. High-CV diagnosis (`cv_diagnosis`)

| | |
|--|--|
| **Idea** | Explain *why* CV is high — distributions, zeros (user vs cohort), per-date whales, trends, sample size, patch maturity |
| **Code** | `experiments/cv_optimization/cv_diagnosis/` |
| **Run** | `runs/2026-08-03_rp_ls_cv_diagnosis_114014/` |
| **Result** | Flagged cases often: broad dispersion, whale share on peak dates, user-level zeros common but **cohort growth_ratio rarely zero**, early patches naturally higher CV. |
| **Verdict** | **diagnostic-only** (keep as reference) |
| **Why** | Clarified drivers; did not change methodology. Motivated “does high CV mean bad goals?” |

---

## 6. CV → OOS predictive backtest (`cv_oos_backtest`)

| | |
|--|--|
| **Idea** | Walk-forward: at historical `T`, freeze patch goal (`mean_after`) + `cv_after` with **no look-ahead**; score next 7/14/30 cohort dates. Ask whether CV predicts OOS error and whether 15% thr has empirical value (esp. `1→7`). |
| **GPT / spec reference** | `experiments/cv_optimization/cv_oos_backtest/GPT_SPEC_walkforward.md` |
| **Code** | `experiments/cv_optimization/cv_oos_backtest/` |
| **Run** | *(pending / add `runs/…_cv_oos_backtest_<ts>/` when exported)* |
| **Result** | TBD |
| **Verdict** | **open** |
| **Why** | Fixing CV (winsor/window/MAD) did not clearly help. Need evidence that high CV actually means unreliable goals before changing thresholds. Separate question from distribution shape. |

---

## 7. Dispersion diagnostics (`dispersion_diagnostics`)

| | |
|--|--|
| **Idea** | When `cv_after` is high: is variability (A) tail-driven, (B) broad in the center (MAD/IQR/P10–P90), or (C) multiplicative/asymmetric (log)? Uses **same** after-trim `growth_ratio`s. Raw `relative_mad_raw` (no ×1.4826); keep `scaled_mad_cv` only for compare. Within-patch ranks + disagreement signals. **Not** a CV replacement; **not** 15% thresholds on new metrics. |
| **Code** | `experiments/cv_optimization/dispersion_diagnostics/marketing_goals_dispersion_diagnostics.ipynb` |
| **Run** | `runs/2026-08-03_rp_ls_dispersion_diagnostics_130742/` |
| **Result** | High CV usually **real / central**, not outlier-only. Example: LS Web `1→7` P10≈1.60, P90≈3.54 after trim (wide center). Log-scale generally agrees with high CV. Exception: RP App `1→7` more center-concentrated / tail-sensitive. LS Web `180→270`: trim cut extremes (`cv_before` ~207% → `cv_after` ~19%) but residual dispersion remains real. `1→7` still naturally high-variability; pops differ inside it. |
| **Verdict** | **diagnostic-only — closed.** Do **not** replace CV with MAD/IQR. |
| **Why / next** | CV is detecting genuine cohort dispersion. Remaining question is predictive: does CV ~20–30% (and that real spread) mean a less reliable Marketing Goal? → **`cv_oos_backtest`**. |

---

## Earlier offline knob replays (pre–Option B)

| | |
|--|--|
| **Location** | `experiments/cv_optimization/offline_2026-08-03/` (scripts + `cv_results_2026-08-03/`) |
| **Ideas** | e.g. early-patch `max_remove` 25%, greedy rank variants |
| **Note** | Softest prior lever was `A_early_max25`; greedy/A25+B moved goals too much. Not production-locked. |
| **Verdict** | **park** (context only) |

---

## Working theory (as of 2026-08-13)

1. Early patches (esp. `1→7`) have **naturally higher CV**; treating them like mature patches with one universal 15% flag may be wrong — **needs OOS proof**.
2. High CV is usually **genuine central dispersion** (dispersion_diagnostics + robust_cv), not “SD inflated by a few outliers.” MAD/IQR replacement **rejected**.
3. Lookback escalation **rejected**; dynamic winsor **parked pending manager** (not a closed reject).
4. Main open gate: **`cv_oos_backtest`** — does CV ~20–30% (real spread) predict worse OOS goal error? Then decide patch-specific expectations vs keep universal thr. Parallel: manager call on winsor escalation.

---

## Do not lock yet

- No change to production `cv_threshold` / `cv_good_enough` / `TRIM_CONFIG` / lookback 35 in generic notebooks or YAML until Lee decides after OOS backtest (and any follow-ups).
