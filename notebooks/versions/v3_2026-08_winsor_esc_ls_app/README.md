*Lee Jerusalmy*

# v3 — winsor_escalation Combined + LS App

Frozen archive of the v2 capped `winsor_escalation` Combined Colab, plus LoneStar App bootstrap.

| File | Purpose |
|------|---------|
| `Marketing_Goals_Combined_RP_LS_Colab_v3_winsor_esc_ls_app.ipynb` | Colab: winsor_esc for other pops + LS App `native_early_rp_tail` |

Source workstream:
- `experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`
- `experiments/ls_app_bootstrap/NOTES.md`
- `playbook/handoffs/LS_APP.md`
- Combined export: `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`
- Draft BQ: `analytics_team.combined_goals_draft`

What this freeze includes:
- RP all pops + LS Web / Affiliate / Blended: capped winsor_esc (`pct_used` wired into the curve)
- LS App: `affid = 1` → App; winsor locked 0%; native through last measured day, then RP App day-growth
- LS Blended excludes App
- LS App organic off (`organic_share = 0`)

Still provisional. Not merged into generic `notebooks/`. Not a `DECISIONS.md` lock.  
Open: leftover pre-launch `affid=1` inside App; launch floor not applied. `AS_OF_DATE` pinned to 2026-08-03.

Do not edit files in this folder — treat as archive.
