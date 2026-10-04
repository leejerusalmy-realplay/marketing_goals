*Lee Jerusalmy*

# RP `app_affiliate` → Affiliate

Working copy for Combined freeze **v4**.

**How it works:** `NOTES.md`  
**New-chat handoff:** `playbook/handoffs/RP_APP_AFFILIATE.md`  
**Frozen archive:** `notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/`

## Colab (open this)

`Marketing_Goals_Combined_RP_LS_Colab_rp_app_affiliate_to_aff.ipynb`

- Base: v3 Combined + RP `channel_type = app_affiliate` → Affiliate. Remaining `APP` stays App.
- **LS:** unchanged (App still `APP` and `cost_date >= 2026-08-05`).
- Matching export: `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`
- Compare-to (last v3-mapping run): `runs/2026-08-19_rp_ls_winsor_esc_ls_app_105632/`

Excel check: `sql/01_rp_app_affiliate_move.sql`

## Do not

- Edit version archives or generic `notebooks/` Combined
- Apply this carve-out to LoneStar
