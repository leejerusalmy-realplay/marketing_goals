# Handoff — CV cleanup optimization (flag rate)

*Lee Jerusalmy*  
**Date:** 2026-08-06  
**Parent work:** marketing goals unified Colab / Combined rebuild  

---

## Goal for this agent

**Reduce the share of patches that remain above the brand CV flag line** after the existing adaptive date-drop step.

Current production-ish thresholds (do not change silently without Lee):

| Brand | Flag if `cv_after` > | Good-enough stop while dropping | Max dates removable |
|-------|----------------------|----------------------------------|---------------------|
| RP | **0.15** | 0.10 | 15% of lookback (~5 of 35) |
| LS | **0.175** | 0.10 | 15% of lookback (~5 of 35) |

**Baseline (run `2026-08-03_rp_ls`, as_of 2026-08-03):**  
**9 / 70 patches flagged (~12.9%)** — all hit max remove (kept=30) except diagnostics below.

Important product rule today: **flag ≠ drop patch.** Flagged patches **still feed the curve**. Optimization targets *fewer / lower flags*, not deleting life windows, unless Lee explicitly asks for a “drop patch” product change.

---

## Flagged patches only (TRUE) — baseline

| brand | population | patch | cv_before | cv_after | n kept | notes |
|-------|------------|-------|-----------|----------|--------|-------|
| realprize | Web | 1→7 | 0.36 | **0.24** | 30 | early life, max drop |
| realprize | Web | 7→14 | 0.22 | **0.15** | 30 | barely over 0.15 |
| realprize | Web | 14→30 | 0.54 | **0.22** | 30 | worst RP start |
| realprize | Web | 30→60 | 0.27 | **0.20** | 30 | |
| realprize | App | 1→7 | 0.34 | **0.22** | 30 | winsor% = 0 |
| realprize | Blended | 1→7 | 0.28 | **0.19** | 30 | winsor% = 0 |
| lonestar | Web | 1→7 | 0.44 | **0.32** | 30 | worst LS early |
| lonestar | Web | 180→270 | 2.07 | **0.19** | 30 | extreme start, long patch |
| lonestar | Blended | 1→7 | 0.31 | **0.24** | 30 | |

Pattern: **early 1→7** (and short early Web patches on RP) + **one LS long-horizon Web outlier**.

Affiliate (both brands) generally clean after cleanup. Many mid/late patches land ≤ flag line.

Full CSV:  
`marketing_goals/runs/2026-08-03_rp_ls/combined_cv_summary.csv`  
(also pasted entire table in user message for this chat.)

---

## Where the code lives

Do **not** edit `reference/`.

| Path | Role |
|------|------|
| `notebooks/Marketing_Goals_Combined_RP_LS.ipynb` | Cursor/local twin |
| `notebooks/Marketing_Goals_Combined_RP_LS_Colab.ipynb` | Colab twin — keep in sync if you change helpers |
| Adaptive CV | `patch_cv_adaptive` in helper cells (CV loop: while CV > 0.10 and removals < max, drop worst |growth − unweighted mean| date) |
| Config knobs | notebook config + `config/realprize.yaml` / `config/lonestar.yaml` |
| Methodology | `playbook/LS_PIPELINE_FLOW.md` Box 8 + Google Doc CV addendum |

Docs: https://docs.google.com/document/d/1rTx9-CdjUaaOESO6D0kRY-xtJ5TkwwIbG1Ia3ObzMns/edit  

---

## Constraints from owner (Lee)

1. Explain choices in analyst language; small experiments before full rewrites.
2. Prefer **cheap** tests: re-run CV on cached growth-by-date if possible; avoid full dual-brand BQ every tweak.
3. Changing knobs (max_remove_fraction, stop rule, ranking of “worst” day, winsor interaction) needs a short **before/after table** on the same as_of: flag count, list of remaining flags, and 2–3 example **goal ratios** so we see if goals move a lot.
4. Do not silently raise flag thresholds just to “green” the report — that’s cheating metrics. Prefer better cleanup or clearer exceptions.
5. SQL Excel-check culture still applies for any *new* formula.

---

## Sensible experiment menu (pick 1–2 first)

1. **Raise max remove** on early patches only (e.g. allow 20–25% dates for 1→7 / 7→14) — measure flag count + mean |Δ ARPU_e/s| on kept set.
2. **Weighted worst-date ranking** (rank by impact on weighted CV, not unweighted |g−μ|) — may pick different 5 days.
3. **Winsor before CV** consistency for Web 1%: confirm growth entering CV is post-winsor (already intended); check if cap strength should rise slightly on flagged Web only.
4. **Floor weights / min $ or N** per cost_date so tiny cohorts don’t dominate CV noise.
5. **Soft policy for long patches** (LS 180→270) if remaining flags are forever outliers — document special case rather than global knobs.
6. **Stop target**: sometimes stop at ≤ flag line (0.15/0.175) instead of insisting on 0.10 when approaching max remove — only if product accepts more aggressive keep under the *flag* bar without chasing 0.10.

---

## Success criteria (proposed)

- Cut flagged patches from **9 → ideally ≤ 4–5** on a replay of the same as_of (or document why remaining flags are irreducible noise).
- No empty patches / no broken day-step curves.
- Blended / Web / App goals still sensible at D7/D30 (spot check); organic untouched.
- Report a **knob table** + before/after flag list.

---

## Experiment results (2026-08-06) — as_of 2026-08-03, no notebook edits yet

**Replay tool:** `experiments/cv_flag_replay_fast.py` + `experiments/cv_knob_replay.py`  
**Cache:** `experiments/cache/2026-08-03/` (users/revenue + `patch_growth_series.parquet`)  
**Outputs:** `experiments/cv_results_2026-08-03/` (`cv_long_all_exps.csv`, `flag_summary.csv`, `spot_goals_compare.csv`)

Baseline offline flags **9/70**, matches run CSV flag set. Thresholds unchanged.

| Experiment | Flag count | Knob notes |
|------------|------------|------------|
| baseline | **9/70** | max_remove=0.15, rank=|g−μ_unw| |
| A_early_max25 | **6/70** | early patches (1→7…30→60) max_remove=0.25 (~8 of 35) |
| A_early_max30 | **6/70** | early max 0.30 — same flags as 25; diminishing returns |
| B_greedy_cv | **6/70** | same 0.15 cap; greedily drop date that most reduces weighted CV |
| **A25+B** | **4/70** | early max 0.25 + greedy rank — hits ≤4–5 target |
| D_global_max25 | 6/70 | global 0.25; no better than early-only |
| C_wdev_early25 | 9/70 | rank |g−μ_w|×weight_share — **worse** (can raise CV) |

### Remaining flags (after best pure levers)

**A_early_max25 (6):** LS Web & Blended 1→7, LS Web 180→270, RP Blended 1→7 (cv 0.159 barely over), RP Web 1→7, RP Web 30→60.

**A25+B (4):** LS Web & Blended 1→7, RP Web 1→7 (0.198), RP Web 30→60 (0.157).

### Spot raw goal impact (1 / product of cleaned patch `mean_after`; validates 0.00% vs production on baseline D1/H7/H30)

| Slice | A_early_max25 | B_greedy | A25+B |
|-------|---------------|----------|-------|
| RP Web d1/h7 | −1.8% | +5.9% | **+11.8%** |
| RP Web d1/h30 | +3.8% | +16.4% | **+25.1%** |
| LS Web d1/h7 | −3.2% | −14.3% | **−19.0%** |
| RP App d1/h7 | +1.2% | −4.7% | +3.2% |

### Recommendation (pending Lee)

1. **Default product candidate: A_early_max25 only** — cuts flags 9→6 with single-digit goal moves. Code: early-patch-aware `max_remove_fraction` in `patch_cv_adaptive`.
2. **A25+B only if flag rate is priority** and product accepts large early-LS / mid-RP Web goal shifts.
3. **Greedy rank alone** good for LS 180→270 (clears with same 5 drops) but moves early means harder — optional second commit after A.
4. **Do not ship C_wdev.** Special-case LS 180→270 only if remaining after A is acceptable to leave flagged (already product: flag ≠ drop).
5. Notebooks still production baseline; wire knobs only after approval.

---

## Paste into a new Cursor chat

```
Continue marketing goals CV optimization in lee_project/marketing_goals/.

Read playbook/CV_OPTIMIZATION_HANDOFF.md first (or this whole message).

Baseline: run 2026-08-03_rp_ls — 9/70 patches flagged (cv_after > 0.15 RP / 0.175 LS).
Almost all early 1→7 (+ RP Web short patches + LS Web 180→270). They already removed max ~5/35 dates.

Goal: reduce flag rate without silent threshold cheat; flag still means keep patch (unless I approve a product change).
Code: notebooks Marketing_Goals_Combined_RP_LS*.ipynb patch_cv_adaptive — do not edit reference/.
Show small experiments first with before/after flag table + spot goal impact.
CSV: runs/2026-08-03_rp_ls/combined_cv_summary.csv
```
