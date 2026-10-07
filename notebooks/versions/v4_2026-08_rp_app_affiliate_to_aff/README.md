*Lee Jerusalmy*

# v4 — v3 + RP `app_affiliate` → Affiliate

**Previous Combined freeze** (2026-08-24). Superseded as current pack by **v5** (`v5_2026-10_stg_deposits_marketing/`) on 2026-10-07. Generic `notebooks/Marketing_Goals_Combined_RP_LS*.ipynb` stay the no-App baseline.

| File | Purpose |
|------|---------|
| `Marketing_Goals_Combined_RP_LS_Colab_v4_rp_app_affiliate_to_aff.ipynb` | Colab: v3 engine + RP `channel_type = app_affiliate` → Affiliate |

Working copy (same code):  
`experiments/rp_app_affiliate_to_aff/Marketing_Goals_Combined_RP_LS_Colab_rp_app_affiliate_to_aff.ipynb`

Matching export: `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`  
Compared to last v3-mapping run: `runs/2026-08-19_rp_ls_winsor_esc_ls_app_105632/`  
Topic write-up: `experiments/rp_app_affiliate_to_aff/NOTES.md` · `playbook/handoffs/RP_APP_AFFILIATE.md`

What this freeze adds on top of v3:

- **RP only:** `channel_type = app_affiliate` → Affiliate (`scope = non_app`, `bucket = acquired`)
- Remaining RP `APP` stays App
- **LS mapping unchanged** (App still `APP` and `cost_date >= 2026-08-05`)
- Same v3 engine: capped winsor_esc, LS App `native_early_rp_tail`, App organic off, `AS_OF_DATE` pinned **2026-08-19**

Still provisional. Not merged into generic `notebooks/`. Not a production YAML lock.

Do not edit files in this folder — treat as archive. Change the working Colab, then replace this freeze when Lee asks.
