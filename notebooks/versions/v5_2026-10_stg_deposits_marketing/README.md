*Lee Jerusalmy*

# v5 — staging marketing deposits

**Current Combined freeze** (2026-10-07). Same engine as v4. Only the deposit source changed.

| File | Purpose |
|------|---------|
| `Marketing_Goals_Combined_RP_LS_Colab_v5_stg_deposits_marketing.ipynb` | Colab: v4 mapping + deposits from `analytics.stg_*_casino_deposits_marketing` |

Working copy (same code):  
`experiments/rp_app_affiliate_to_aff/Marketing_Goals_Combined_RP_LS_Colab_rp_app_affiliate_to_aff.ipynb`

Deposit tables:

- RealPrize: `analytics.stg_realprize_casino_deposits_marketing`
- LoneStar: `analytics.stg_lonestar_casino_deposits_marketing`

Query columns: `user_id`, `deposit_date`, `deposit_amount` (already USD), `deposit_status = 'APPROVED'`.  
User tables stay `analytics.realprize_cost_per_user` and `analytics.lonestar_cost_per_user`.

`AS_OF_DATE` in this file is pinned **2026-10-02**. Saved notebook outputs and `runs/2026-10-02_rp_ls_rp_app_affiliate_to_aff_123941/` are still the **Astropay** export. Re-run Colab before treating goals as coming from these staging tables.

What stays from v4:

- RP `channel_type = app_affiliate` → Affiliate (`scope = non_app`, `bucket = acquired`)
- Remaining RP `APP` stays App
- LS App: `APP` and `cost_date >= 2026-08-05`; earlier APP → Affiliate
- Capped winsor_esc, LS App `native_early_rp_tail`, App organic off

v4 stays archived. Generic `notebooks/` Combined stay the no-App baseline.

Do not edit files in this folder — treat as archive. Change the working Colab, then replace this freeze when Lee asks.
