*Lee Jerusalmy*

# Topic handoff — LS App goals (bootstrap)

**Read after** main `playbook/HANDOFF.md`.  
**Opened:** 2026-08-18 — LS App launched 2026-07-16; not enough native history for a normal Combined lock.  
**Last updated:** 2026-08-18 — leftover `affid=1` found; launch floor not applied yet.

---

## Paste into a new agent chat

```
Continue marketing goals — LS App bootstrap.
Read playbook/HANDOFF.md first, then playbook/handoffs/LS_APP.md
and experiments/ls_app_bootstrap/NOTES.md.
Don’t re-teach the full pipeline. Don’t edit reference/.
Don’t lock into generic notebooks/ or DECISIONS.md.
Lee’s current Combined freeze is v3 winsor_esc + LS App
(notebooks/versions/v3_2026-08_winsor_esc_ls_app/), not generic Combined.
```

---

## Where the files are

| | |
|--|--|
| **Experiment home** | `experiments/ls_app_bootstrap/` |
| **How to calculate (write-up)** | `experiments/ls_app_bootstrap/NOTES.md` |
| **Colab to open** | `experiments/ls_app_bootstrap/Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb` |
| **Python twin (do not run unprompted)** | `experiments/ls_app_bootstrap/build_winsor_esc_plus_ls_app.py` |
| **Method compare** | `experiments/ls_app_bootstrap/run_ls_app_bootstrap.py` |
| **Method-compare export** | `runs/2026-08-17_ls_app_bootstrap_114318/` |
| **Combined export (Colab)** | `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/` |
| **v3 freeze (this Colab)** | `notebooks/versions/v3_2026-08_winsor_esc_ls_app/` |
| **v2 winsor freeze (no App)** | `notebooks/versions/v2_2026-08_winsor_escalation_combined/` |

Lee treats **v3 winsor_esc + LS App** as her current Combined freeze. Generic `notebooks/Marketing_Goals_Combined_RP_LS*.ipynb` stay baseline. v2 stays the no-App winsor archive.

---

## Provisional method (not locked)

**`native_early_rp_tail`**

1. Map `affid = 1` → population App.
2. Same Combined boxes through last **measured** patch (cum / dsi / ARPU / winsor / growth / CV / day-steps / D1).
3. LS App winsor **0%**, **no escalation**.
4. Keep native curve through last non-extrapolated day **S**.
5. After S, do **not** use LS tail extrapolation. Stick RP App day-growth:

   `ARPU(d) = ARPU(d-1) × (ARPU_RP_App(d) / ARPU_RP_App(d-1))`

6. Goals: `raw = ARPU(d)/ARPU(H)`.
7. **LS App organic is off** (`organic_share = 0` → `adjusted = raw`).
8. **LS Blended stays Web + Affiliate only.** App is an add-on.

S is dynamic if `AS_OF_DATE` moves. LS skips a patch when cohort dates &lt; **20**.  
Colab still has `AS_OF_DATE` pinned to **2026-08-03** → this run **S = 14**.  
A later as_of (~mid-Sep) should unlock S = 30, not 60 yet.

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

## Latest Combined Colab run

`runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/`

- ~25.8k LS App users; scope/bucket mapped (app acquired 21,467 / app organic 4,326).
- Winsor stayed 0%. Splice after day **14**. D1 **$6.24** → D14 **$16.97** → D120 **$48.71**.
- App organic **forced to 0** in the export (H120 was NaN; H30 was a misleading 100%).
- **Not a copy of** `runs/2026-08-03_rp_ls_winsor_escalation_143601/`:
  - this Colab **wires `pct_used` into the curve** (143601 still built the curve on floor winsor);
  - `affid=1` left LS Affiliate.
  - Close: RP Affiliate / RP Blended / LS Blended **ratios**. Different: RP Web, RP App, LS Web, LS Affiliate.

---

## Organic (parked)

RP-style `scope` / `bucket` is in the LS users SQL (`app` vs `non_app`; `app_organic`).  
**Do not apply App organic yet.** Too little mature App history:

- H7: a real mix, but ~60% (high vs RP App).
- H30: 100% organic — window ends before launch; leftover old `affid=1` only, 0 acquired.
- H120: empty → NaN.

Leave `organic_share = 0` on LS App until Lee reopens this.

---

## Leftover `affid=1` (open)

Old `affid=1` users (before 2026-07-16) are mapped to App. Detail + Excel SQL: `experiments/ls_app_bootstrap/NOTES.md` and `sql/01_leftover_affid1_vs_app.sql`.

- Combined D1 **$6.24** mixes leftover D1 ~**$9.07** with real App ~**$4.65**.
- Method-compare **S=30** used 22 leftover dates + 3 real App dates. Not 30 days of App history.
- A launch floor (`cost_date >= 2026-07-16`) is **not** in the Colab yet.

## Do now

1. **Decide launch floor** for LS App (`cost_date >= 2026-07-16`). Recommended: yes, then re-run Colab. Do not bump `AS_OF_DATE` alone.
2. If floored: S stays **7** on as_of ~2026-08-16; S=14 around **2026-08-18+**; S=30 around **2026-09-03**.
3. Existing Combined export stays organic = 0. Usable only as a mixed leftover+App draft.
4. Do not treat this as production until she locks.

## Draft BigQuery table (until BI is back)

Lee can query Combined output without waiting for Looker / dbt.

- Table: `analytics_team.combined_goals_draft` (replace each load)
- Loaded 2026-08-18 from `runs/2026-08-03_rp_ls_winsor_esc_ls_app_110733/combined_goals.csv` (13,776 rows)
- Script: `experiments/ls_app_bootstrap/upload_combined_goals_bq.py`
- Do **not** overwrite `analytics.stg_*_marketing_goals_blended_daily` (Looker production, different grain)

## Do not

- Edit `reference/` or generic `notebooks/` Combined.
- Lock `DECISIONS.md`.
- Put LS App into LS Blended unless Lee asks.
- Apply winsor escalation on LS App.
- Use native LS extrapolation to 120.
- Re-run the heavy Combined Colab unless Lee asks.
- Assume non-App cells match `2026-08-03_rp_ls_winsor_escalation_143601`.

---

## Related (parked, other files)

- July freeze winsor_esc vs production: `runs/2026-07-10_rp_ls_goal120_realized_winsor_esc_064344/compare_vs_production.csv` — small `first_day` improvement, not a lock.
- CV OOS: `playbook/handoffs/CV_OPTIMIZATION.md`.
