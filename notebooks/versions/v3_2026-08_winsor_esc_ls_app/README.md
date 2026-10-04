*Lee Jerusalmy*

# v3 — winsor_escalation Combined + LS App

**Previous Combined freeze** (replaced 2026-08-19). Superseded as current pack by **v4** (`v4_2026-08_rp_app_affiliate_to_aff/`) on 2026-08-24. Generic `notebooks/Marketing_Goals_Combined_RP_LS*.ipynb` stay the no-App baseline.

| File | Purpose |
|------|---------|
| `Marketing_Goals_Combined_RP_LS_Colab_v3_winsor_esc_ls_app.ipynb` | Colab: winsor_esc for other pops + LS App `native_early_rp_tail` |

Working copy (same code):  
`experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb`

Matching export: `runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/`  
Topic write-up: `experiments/ls_app_bootstrap/NOTES.md` · `playbook/handoffs/LS_APP.md`

What this freeze includes:

- RP all pops + LS Web / Affiliate / Blended: capped winsor_esc (`pct_used` wired into the curve)
- LS App: `marketing_population = APP` **and** `cost_date >= 2026-08-05` → App; earlier APP stays Affiliate
- LS App winsor locked **0%** (no escalation); `min_cohort_dates = 1` (temporary); Web / Aff / Blended stay **20**
- Native curve through last measured day, then RP App day-growth (`native_early_rp_tail`)
- LS App organic off (`organic_share = 0`)
- CV export: App-pipeline Blended rows dropped, so LS Blended appears once
- `AS_OF_DATE` pinned **2026-08-19**; splice after day **14**

Intent: LS Blended is Web + Affiliate + PPC + Organic (App as add-on). PART 2 still copies all `users_df` rows, so some App users still sit in the Blended curve.

Still provisional. Not merged into generic `notebooks/`. Not a production YAML lock.

**2026-08-20:** users SQL uses `marketing_population` (SEO + Shared Link + RP 2290 → Organic; TikTok WEB still excluded). Lee asked to update this freeze folder.

Supersedes the 2026-08-18 freeze of this folder (mixed leftover `affid=1` in App, no floor, as_of 2026-08-03). That pack stays at `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`.

Do not edit files in this folder — treat as archive. Change the working Colab, then replace this freeze when Lee asks.
