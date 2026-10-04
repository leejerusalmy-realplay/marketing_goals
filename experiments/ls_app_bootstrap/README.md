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
- LS App: `marketing_population = APP` and `cost_date >= 2026-08-05` → App (earlier APP stays Affiliate); winsor locked at **0%**; App `min_cohort_dates = 1` (temporary); then `native_early_rp_tail`.
- LS Blended stays Web+Affiliate only.
- LS App organic **off** (`organic_share = 0`).

v3 Combined export: `runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/`  
Current Combined freeze is **v4** (same LS App method): `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`  
(old mixed leftover pack: `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`)

## Method compare

```bash
python "experiments/ls_app_bootstrap/run_ls_app_bootstrap.py" --count-only
python "experiments/ls_app_bootstrap/run_ls_app_bootstrap.py"
```

Export: `runs/2026-08-17_ls_app_bootstrap_114318/`  
Main verdict: `method_summary.csv` (lower `shape_mae` wins per slice).

Provisional H=120 candidate: **`native_early_rp_tail`**. Native-to-120 explodes (~$6,855). Not locked.

**Open (history):** leftover `affid=1` used to sit inside App. Current freeze floors App at **2026-08-05**; earlier `affid=1` is Affiliate. Excel SQL: `sql/01_leftover_affid1_vs_app.sql`.

## Do not

- Move this into generic `notebooks/` until Lee asks
- Fold App into LS Blended
- Apply winsor escalation on LS App
- Use LS tail extrapolation on App
- Treat non-App cells as a copy of `runs/2026-08-03_rp_ls_winsor_escalation_143601/`
