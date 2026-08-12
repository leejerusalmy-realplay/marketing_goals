*Lee Jerusalmy*

# CV optimization experiments (index)

Parallel CV knob trials live here. **Generic Combined notebooks stay under `notebooks/`** (clean baseline code). Each variant has its own Colab copy + run exports.

**Experiment log (results + reject/keep reasons):** [`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md) — read this for learning across chats.

## Layout

```text
experiments/cv_optimization/
  README.md                 ← this index
  baseline/                 ← pointer to frozen baseline run
  winsor_escalation/        ← Colab with winsor-pct ladder (+ revenue cut)
  window_escalation/        ← Colab with lookback window ladder (no winsor ladder)
  robust_cv/                ← Colab: existing CV + Robust CV diagnostics (side-by-side)
  cv_diagnosis/             ← exploratory: why is CV high? (no methodology change)
  cv_oos_backtest/          ← walk-forward: does CV predict OOS goal error?
  offline_2026-08-03/       ← early Python knob replays (NOT Colab runs/)
runs/
  2026-08-03_rp_ls/                              ← baseline numbers
  2026-08-03_rp_ls_<ts>/                         ← older winsor test runs
  2026-08-03_rp_ls_window_escalation_<HHMMSS>/   ← window test runs
  2026-08-03_rp_ls_robust_cv_<HHMMSS>/           ← robust CV compare runs
  2026-08-03_rp_ls_cv_diagnosis_<HHMMSS>/        ← CV diagnosis exports
  2026-08-03_rp_ls_cv_oos_backtest_<HHMMSS>/     ← walk-forward backtest exports
```

## Variant table

| Variant | What changed | Notebook | as_of | Run folder(s) | Flags vs baseline | Status |
|---------|--------------|----------|-------|---------------|-------------------|--------|
| **baseline** | Production knobs (LS flag thr 0.175, lookback 35, static winsor) | `notebooks/Marketing_Goals_Combined_RP_LS*_` (generic) | 2026-08-03 | `runs/2026-08-03_rp_ls/` | 9 / 70 flagged | reference |
| **winsor_escalation** | Per-patch winsor ladder + abs 15% $ cut; AS_OF pinned | `…/winsor_escalation/` | 2026-08-03 | `…_143601/`, `…_133829/` | 9→8 (capped) | **park — check with manager** |
| **window_escalation** | Lookback 35→65; LS thr 0.15 | `…/window_escalation/` | 2026-08-03 | `…_window_escalation_080607/` | 9→8 | **reject** |
| **union patches** | GPT idea — not implemented | — | — | — | — | **reject** (discarded) |
| **robust_cv** (MAD) | Robust CV alongside CV; not a replacement | `…/robust_cv/` | 2026-08-03 | `…_robust_cv_111132/` | flagged mostly consistent variability | **reject as replace** / diagnostic |
| **cv_diagnosis** | Why is CV high? | `…/cv_diagnosis/` | 2026-08-03 | `…_cv_diagnosis_114014/` | — | **diagnostic-only** |
| **cv_oos_backtest** | Walk-forward: does CV predict OOS goal error? | `…/cv_oos_backtest/` (+ `GPT_SPEC_walkforward.md`) | 2026-08-03 | *(pending export)* | production thr | **open — current focus** |

## How to run a variant

1. Open that variant’s Colab under `experiments/cv_optimization/<name>/`.
2. Runtime → Run all (mount Drive if you want CSVs under `marketing_goals/runs/`).
3. Export lands in `runs/<as_of>_rp_ls_<experiment_tag>_<HHMMSS>/`.
4. Update the **Status** / **Run folder** cells in this table.

## Rules

- Do **not** put experiment knobs into the generic `notebooks/` Colab until Lee locks a winner.
- Do **not** overwrite `runs/2026-08-03_rp_ls/` or another variant’s CSVs.
- Topic handoff: `playbook/handoffs/CV_OPTIMIZATION.md`.
