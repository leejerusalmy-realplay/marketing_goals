*Lee Jerusalmy*

# LS App bootstrap tests

Goal: choose the best temporary method for `lonestar/App` goals while post-launch history is still short.

Launch note:
- LS App launched on **2026-07-16**.
- Early work is **provisional**, not a locked production methodology.

**How to calculate + what we checked:** `NOTES.md`  
**New-chat handoff:** `playbook/handoffs/LS_APP.md`

## Combined Colab (open this)

`Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`

Open in Colab → Runtime → Run all. Python twin `build_winsor_esc_plus_ls_app.py` — do not run unless asked.

- Base: archived v2 winsor_esc Combined, with `pct_used` wired.
- RP all pops + LS Web / Affiliate / Blended: capped winsor_esc.
- LS App: `affid=1` → App; winsor locked at **0%**; then `native_early_rp_tail`.
- LS Blended stays Web+Affiliate only.
- LS App organic **off** (`organic_share = 0`).

Latest Combined export: `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`

## Method compare

```bash
python "experiments/ls_app_bootstrap/run_ls_app_bootstrap.py" --count-only
python "experiments/ls_app_bootstrap/run_ls_app_bootstrap.py"
```

Export: `runs/2026-08-17_ls_app_bootstrap_114318/`  
Main verdict: `method_summary.csv` (lower `shape_mae` wins per slice).

Provisional H=120 candidate: **`native_early_rp_tail`**. Native-to-120 explodes (~$6,855). Not locked.

**Open:** leftover `affid=1` (pre-launch) sits inside App. Excel SQL: `sql/01_leftover_affid1_vs_app.sql`. Do not bump `AS_OF_DATE` until a launch floor is decided.

## Do not

- Move this into generic `notebooks/` or `DECISIONS.md` until Lee locks
- Fold App into LS Blended
- Apply winsor escalation on LS App
- Use LS tail extrapolation on App
- Treat non-App cells as a copy of `runs/2026-08-03_rp_ls_winsor_escalation_143601/`
