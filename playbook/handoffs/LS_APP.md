*Lee Jerusalmy*

# Topic handoff — LS App goals (bootstrap)

**Read after** main `playbook/HANDOFF.md`.  
**Opened:** 2026-08-18 — LS App launched 2026-07-16; not enough native history for a normal Combined lock.  
**Last updated:** 2026-10-07 — Combined current freeze is **v5** (LS App method unchanged; deposits now staging tables). App start 2026-08-05; App `min_cohort_dates = 1` (temporary). Provisional vs generic Combined.

---

## Paste into a new agent chat

```
Continue marketing goals — LS App bootstrap.
Read playbook/HANDOFF.md first, then playbook/handoffs/LS_APP.md
and experiments/ls_app_bootstrap/NOTES.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Don’t copy into generic notebooks/ until Lee asks.
Lee’s current Combined freeze is v5 (includes this LS App method; deposits from staging tables).
LS App method is unchanged from v3. Current pack:
notebooks/versions/v5_2026-10_stg_deposits_marketing/
Matching export: runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/
v3 archive: notebooks/versions/v3_2026-08_winsor_esc_ls_app/
v3 export: runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/
```

---

## Where the files are

| | |
|--|--|
| **Experiment home** | `experiments/ls_app_bootstrap/` |
| **How to calculate (write-up)** | `experiments/ls_app_bootstrap/NOTES.md` |
| **Colab to open** | `experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb` |
| **Current Combined freeze** | `notebooks/versions/v5_2026-10_stg_deposits_marketing/` (LS App method unchanged; deposits from staging tables) |
| **v3 archive** | `notebooks/versions/v3_2026-08_winsor_esc_ls_app/` (replaced 2026-08-19) |
| **Python twin (do not run unprompted)** | `experiments/ls_app_bootstrap/build_winsor_esc_plus_ls_app.py` — lags the Colab floor |
| **Method compare** | `experiments/ls_app_bootstrap/run_ls_app_bootstrap.py` |
| **Method-compare export** | `runs/2026-08-17_ls_app_bootstrap_114318/` |
| **Current Combined export** | `runs/2026-08-19_rp_ls_rp_app_affiliate_to_aff_112133/` |
| **v3 Combined export** | `runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/` |
| **Old mixed export (keep)** | `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/` |
| **v2 winsor freeze (no App)** | `notebooks/versions/v2_2026-08_winsor_escalation_combined/` |

Lee treats **v3 winsor_esc + LS App** as her current Combined freeze. Generic `notebooks/Marketing_Goals_Combined_RP_LS*.ipynb` stay the no-App baseline.

---

## Provisional method (current freeze)

**`native_early_rp_tail`**

1. Map `marketing_population = APP` **and** `cost_date >= 2026-08-05` → population App. Earlier APP stays Affiliate.
2. Same Combined boxes through last **measured** patch (cum / dsi / ARPU / winsor / growth / CV / day-steps / D1).
3. LS App winsor **0%**, **no escalation**.
4. Keep native curve through last non-extrapolated day **S**.
5. After S, do **not** use LS tail extrapolation. Stick RP App day-growth:

   `ARPU(d) = ARPU(d-1) × (ARPU_RP_App(d) / ARPU_RP_App(d-1))`

6. Goals: `raw = ARPU(d)/ARPU(H)`.
7. **LS App organic is off** (`organic_share = 0` → `adjusted = raw`).
8. **LS Blended intent:** Web + Affiliate + PPC + Organic. App is an add-on. PART 2 still copies all `users_df`, so some App users still sit in the Blended curve.
9. CV concat keeps only `population == App` from the App pipeline pass, so LS Blended CV is not duplicated.

S is dynamic if `AS_OF_DATE` moves. LS Web / Affiliate / Blended skip a patch when cohort dates &lt; **20**.  
**LS App:** `min_cohort_dates = 1`. Colab: `LS_APP_START_DATE = 2026-08-05`, `AS_OF_DATE` pinned **2026-08-19**.

---

## Method-compare checks (why this method)

Export: `runs/2026-08-17_ls_app_bootstrap_114318/`  
Score = short-horizon **shape so far** on a fixed user set (`ARPU(d)/ARPU(D*)`). Do not pick on D120 fit.

| Method | D30 ARPU | D120 ARPU | Notes |
|--------|---------:|----------:|-------|
| `native_ls_app` | 24.77 | **6,855** | LS extrapolate explodes — do not use |
| `native_early_rp_tail` | 24.77 | **48.45** | Provisional H=120 candidate |
| `ls_web_donor` | 21.39 | 48.96 | |
| `hybrid_donor` | 20.23 | 43.14 | |
| `rp_app_donor` | 19.08 | 37.33 | Best on `launch_day` only |

- `launch_day` (16 Jul, D*=33): **rp_app_donor** (shape MAE 0.274); native_early 3rd.
- `launch_week` (16–22 Jul, D*=27): **native_early** ties native (0.083); rp_app last.

Keep native early (better on the first-week wave); dress RP App only after measured history ends.

---

## Latest Combined Colab run (current freeze)

`runs/2026-08-19_rp_ls_winsor_esc_ls_app_074309/`

- App start 2026-08-05; App `min_cohort_dates = 1`; pre-5/8 `affid=1` → Affiliate
- LS App: patch 1→7 = 8 dates / 8,020 users; patch 7→14 = **1 date** (5 Aug) / 1,004 users
- Winsor stayed 0%. Splice after day **14**. D1 **$3.95** → D14 **$23.13** → D120 **$64.07**
- App organic **0**. LS Web/Aff H120 organic share **33.3%** (`non_app`)
- CV: LS Blended once (App-pass Blended rows dropped after the run and in the Colab concat)

Old mixed pack (do not use as current): `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`  
leftover `affid=1` inside App, D1 **$6.24**, as_of 2026-08-03.

---

## Organic (parked)

RP-style `scope` / `bucket` is in the LS users SQL (`app` vs `non_app`; `app_organic`).  
**Do not apply App organic yet.** Too little mature App history.

Leave `organic_share = 0` on LS App until Lee reopens this.

---

## Leftover `affid=1`

Old `affid=1` before launch used to sit in App. Detail + Excel SQL: `experiments/ls_app_bootstrap/NOTES.md` and `sql/01_leftover_affid1_vs_app.sql`.

**Current freeze:** App start **2026-08-05**. Pre-5/8 `affid = 1` → **Affiliate**. That also moves those users in the LS core load (Affiliate / Blended).

---

## Do now

1. Current Combined pack is v4 + `…112133`. LS App method is unchanged. Do not re-run Combined unless Lee asks.
2. App organic stays off.
3. Do not copy into generic Combined / YAML until Lee asks.
4. Do not run the Python twin for this freeze (floor / App gate still lag the Colab).

## Draft BigQuery table (until BI is back)

Lee can query Combined output without waiting for Looker / dbt.

- Table: `analytics_team.combined_goals_draft` (replace each load)
- Last loaded 2026-08-18 from `…110733` (mixed pack). Point `upload_combined_goals_bq.py` at `…074309` before the next load.
- Script: `experiments/ls_app_bootstrap/upload_combined_goals_bq.py`
- Do **not** overwrite `analytics.stg_*_marketing_goals_blended_daily` (Looker production, different grain)

## Do not

- Edit `reference/` or generic `notebooks/` Combined.
- Put LS App into LS Blended on purpose (intent is add-on; PART 2 still copies `users_df`).
- Apply winsor escalation on LS App.
- Use native LS extrapolation to 120.
- Re-run the heavy Combined Colab unless Lee asks.
- Treat `…110733` or `…143601` as the current Combined pack.

---

## Related (parked, other files)

- July freeze winsor_esc vs production: `runs/2026-07-10_rp_ls_goal120_realized_winsor_esc_064344/compare_vs_production.csv` — small `first_day` improvement, not a lock.
- CV OOS: `playbook/handoffs/CV_OPTIMIZATION.md`.
