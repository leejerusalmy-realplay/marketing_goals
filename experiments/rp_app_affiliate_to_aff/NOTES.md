*Lee Jerusalmy*

# RP `app_affiliate` → Affiliate — notes

## Setup

- Experiment home / working copy: `experiments/rp_app_affiliate_to_aff/`
- Colab: `Marketing_Goals_Combined_RP_LS_Colab_rp_app_affiliate_to_aff.ipynb`
- **Current Combined freeze (v5, 2026-10-07):** `notebooks/versions/v5_2026-10_stg_deposits_marketing/` (deposits from `analytics.stg_*_casino_deposits_marketing`; mapping unchanged)
- **Previous freeze (v4, 2026-08-24):** `notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/`
- Topic handoff: `playbook/handoffs/RP_APP_AFFILIATE.md`
- Matching export: `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/`
- Compare-to (last v3-mapping run): `runs/2026-08-19_rp_ls_winsor_esc_ls_app_105632/`

Not copied into generic Combined or YAML. Not a production lock.

## Rule (RP only)

On `analytics.realprize_cost_per_user`:

1. Existing exceptions stay: SEO / Shared Link / affid `2290` → Organic; TikTok WEB `4313` excluded.
2. `channel_type = app_affiliate` → Goals **Affiliate**, `scope = non_app`, `bucket = acquired`.
3. Remaining `marketing_population = APP` stays **App**.
4. LoneStar users SQL is the v3 SQL. No carve-out.

After mapping, the rest of Combined is v3: winsor_esc, CV, day-steps, organic, LS App `native_early_rp_tail`.

## What moved vs last Combined (`…105632`)

- H120 window: ~5.6k RP users App → Affiliate
- RP App H120 adjusted 0.794 → 0.715 (organic 20.6% → 28.5%)
- RP Affiliate / Web H120 adjusted 0.398 → 0.466 (non_app organic 60.2% → 53.4%)
- RP Web ARPU unchanged; Web goals moved via shared non_app organic
- RP Blended almost flat
- LS App identical through day 14; D15+ follows the new RP App tail

## Excel

`sql/01_rp_app_affiliate_move.sql` — 14-day RP counts: v3 label vs this mapping.
