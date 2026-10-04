*Lee Jerusalmy*

# Topic handoff — RP `app_affiliate` → Affiliate

**Read after** main `playbook/HANDOFF.md`.  
**Opened:** 2026-08-23 — Combined experiment, RealPrize only.  
**Last updated:** 2026-08-24 — **promoted to Combined freeze v4**.

---

## Paste into a new agent chat

```
Continue marketing goals — current Combined freeze is v4
(RP app_affiliate → Affiliate; LS mapping unchanged).
Read playbook/HANDOFF.md first, then playbook/handoffs/RP_APP_AFFILIATE.md
and experiments/rp_app_affiliate_to_aff/NOTES.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Don’t edit notebooks/versions/ (archives). Don’t apply the carve-out to LoneStar.
Don’t copy into generic notebooks/ until Lee asks.
Matching export: runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/
```

---

## Where the files are

| | |
|--|--|
| **Current freeze** | `notebooks/versions/v4_2026-08_rp_app_affiliate_to_aff/` |
| **Working Colab** | `experiments/rp_app_affiliate_to_aff/Marketing_Goals_Combined_RP_LS_Colab_rp_app_affiliate_to_aff.ipynb` |
| **Notes** | `experiments/rp_app_affiliate_to_aff/NOTES.md` |
| **Excel SQL** | `experiments/rp_app_affiliate_to_aff/sql/01_rp_app_affiliate_move.sql` |
| **Matching export** | `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/` |
| **Compare-to (last v3-mapping run)** | `runs/2026-08-19_rp_ls_winsor_esc_ls_app_105632/` |
| **Previous freeze** | `notebooks/versions/v3_2026-08_winsor_esc_ls_app/` |

---

## Rule

- **RP:** `channel_type = app_affiliate` → Affiliate (`non_app` / `acquired`). Other `APP` stays App.
- **LS:** v3 mapping. No carve-out.
- Rest of Combined = v3 (`AS_OF_DATE` still **2026-08-19**).

---

## Compare vs last Combined (`…105632`)

- H120 window: ~5.6k RP users App → Affiliate
- RP App H120 adjusted 0.794 → 0.715 (organic share 20.6% → 28.5%)
- RP Affiliate / Web H120 adjusted 0.398 → 0.466 (non_app organic 60.2% → 53.4%)
- RP Web ARPU unchanged; Web goals moved via shared non_app organic
- RP Blended almost flat
- LS mapping unchanged; LS App D15+ moved because the RP App tail donor changed

---

## Do now

1. v4 + `…112133` are the current Combined pack.
2. Do not copy into generic Combined / YAML until Lee asks.
3. Looker `realplay_goals_performance` now uses this v4 user mapping. Goals table upload is Lee’s.

## Do not

- Edit `reference/` or version archives
- Apply this to LoneStar
- Treat v3 `…074309` / `…105632` as the current Combined pack
