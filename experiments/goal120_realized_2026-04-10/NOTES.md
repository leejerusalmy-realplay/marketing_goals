*Lee Jerusalmy*

# Goal-120 realized check — freeze 2026-04-10

One-shot check. **Not** `cv_oos_backtest`. Does not change production knobs.
Does not write into generic notebooks or `DECISIONS.md`.

## Question

If Combined had been run on **2026-04-10**, would the horizon-120 daily goals
have matched what cost_dates **2026-04-10 … 2026-04-14** actually did?

## Locked choices (Lee, 2026-08-16)

| Choice | Value |
|--------|--------|
| `AS_OF_DATE` | **2026-04-10** exactly (not today−2 on that day) |
| Actuals | Raw realized ARPU — **not winsorized** |
| Primary | **Shape:** actual `ARPU(d) / ARPU(120)` vs frozen `raw_goal_ratio` |
| Also in tables | Adjusted ratio + $ level (`ARPU_nominal` is **before** organic) |
| Pull | Patches through **(90, 120)** only; skip 150–365 |

## How to run

**Local / Cursor**

```bash
python "experiments/goal120_realized_2026-04-10/run_goal120_realized.py"
```

Cheap volume check only:

```bash
python "experiments/goal120_realized_2026-04-10/run_goal120_realized.py" --count-only
```

**Colab:** open `goal120_realized_colab.ipynb` and run top → bottom.

## Export

`runs/2026-04-10_rp_ls_goal120_realized_<HHMMSS>/`

Helpers are executed from `notebooks/Marketing_Goals_Combined_RP_LS.ipynb`
(generic Combined). This folder only adds freeze / actuals / compare / export.

## First Colab run (2026-08-16)

Export: `runs/2026-04-10_rp_ls_goal120_realized_133457/`.

The Combined RUN cell also executed first (as_of **2026-08-14**, full horizons) because the helper loader only looked for a line starting with `# RUN`. That dump is `runs/2026-08-14_rp_ls_132733/` — **not** this check. The loader now stops on any Combined RUN/export cell. Do not re-run the full check unless you want a new export.

## Variant: capped winsor_escalation (same freeze / actuals)

Same question, frozen goals from the **capped** trial (escalate winsor toward
`cv_threshold`; **stop if revenue cut > 15% absolute**).

- Helpers: `experiments/cv_optimization/winsor_escalation/Marketing_Goals_Combined_RP_LS_Colab.ipynb`
- Canonical capped run (knob proof): `runs/2026-08-03_rp_ls_winsor_escalation_143601/`
- Do **not** use uncapped `…winsor_escalation_nocap_133829/`
- **Curve wiring:** archived notebook still builds day-steps on floor winsor
  (`pct_used` not passed into `build_curve`). This check wires `pct_used` into
  the curve so the goals actually differ. Check copy only — not generic Combined,
  not the archived notebook, not `DECISIONS.md`.
- Actuals reused from `…_133457/` when that file exists (raw ARPU, same N).

```bash
python "experiments/goal120_realized_2026-04-10/run_goal120_winsor_esc.py"
```

**Colab:** `goal120_winsor_esc_colab.ipynb` — run top → bottom.

Export: `runs/2026-04-10_rp_ls_goal120_realized_winsor_esc_<HHMMSS>/`  
Side-by-side vs production: `compare_vs_production.csv` (primary = shape MAE).
