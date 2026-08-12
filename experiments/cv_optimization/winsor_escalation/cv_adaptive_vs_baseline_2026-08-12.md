*Lee Jerusalmy*

# Adaptive winsor test vs baseline (2026-08-12)

**Baseline:** `runs/2026-08-03_rp_ls/combined_cv_summary.csv`  
**Adaptive (with revenue cap):** `runs/2026-08-03_rp_ls_143601/combined_cv_summary_adaptive_test.csv`  
**Adaptive (no revenue cap, earlier same day):** `runs/2026-08-03_rp_ls_133829/…`

Both adaptive runs: `as_of_date=2026-08-03` (pinned).

---

## Headline (CV summary)

| Metric | Baseline | Adaptive + 15% rev cap (143601) | Adaptive no rev cap (133829) |
|--------|----------|----------------------------------|------------------------------|
| Patches | 70 | 70 | 70 |
| Flagged | 9 | **8** | **3** |
| Escalated above floor | — | 7 | 9 |
| Hit date-remove cap (5/35) | 29 | 29 | (not re-tallied) |

**Only 1 newly unflagged under the revenue cap:** RealPrize Web `7→14` (CV 0.151 → 0.137 at `pct_used=0.02`).

**No newly flagged** vs baseline under the capped run.

---

## Escalations that stuck (143601)

| Brand | Pop | Patch | floor → used | cv_after base → ad | mean_after Δ | rev cut | still flagged? |
|-------|-----|-------|--------------|--------------------|--------------|---------|----------------|
| RP | Web | 7→14 | 1% → 2% | 0.151 → 0.137 | −0.068 | 11.3% | cleared |
| RP | Web | 14→30 | 1% → 2% | 0.221 → 0.194 | −0.059 | 11.2% | yes (capped) |
| RP | Web | 30→60 | 1% → 5% | 0.202 → 0.194 | −0.036 | 12.5% | yes |
| RP | App | 1→7 | 0% → 0.5% | 0.223 → 0.151 | −0.144 | 14.5% | yes (capped) |
| LS | Web | 1→7 | 0% → 0.5% | 0.316 → 0.259 | −0.302 | 9.6% | yes (capped) |
| LS | Web | 14→30 | 0% → 0.5% | 0.159 → 0.127 | −0.049 | 11.2% | no |
| LS | Web | 30→60 | 0% → 0.5% | 0.162 → 0.115 | −0.077 | 10.0% | no |

63/70 patches stayed at floor.

---

## Revenue-cap behavior

- Cap **matters**: without it, flags fall 9→3, but several patches climb to **5%** winsor (RP Web 1→7 / 14→30 / 30→60, LS Web 1→7).
- With cap, those climbs are blocked; RP App / both Blended `1→7` / LS Web `180→270` stay flagged at floor.
- **Diagnostic noise:** all Affiliate patches (floor 1%) show `revenue_cut_fraction` 25–49% and `capped_by_revenue_limit=True` with `n_escalation_steps_tried=1`. Production floor trim already exceeds 15% $ cut — the absolute cut gate marks them “capped” even though CV is fine and no escalation was needed.
- Cleaner gate for a next test: cap **incremental** cut above floor (`cut(pct) − cut(floor) ≤ 0.15`), not absolute cut.

---

## Goals CSVs — do not over-read

`combined_goals` / organic exports differ for reasons beyond adaptive winsor (notably RP App organic at H=90: ~0.340 → ~0.278). Curve day-steps also still use config-floor winsor (`pct_used` not wired into `build_curve`). Treat goal deltas as **contaminated** for this decision; use CV summary only.

---

## Recommendation (for Lee)

1. **Do not lock** adaptive winsor into production / YAML / `DECISIONS.md` yet — under the absolute 15% cut it barely moves flags (9→8).
2. **Do not revert `AS_OF_DATE` for a “ship”** until a re-test; keep pin while iterating.
3. **Next code tweak (preferred before `build_curve`):** redefine revenue stop as incremental-above-floor; re-export `*_adaptive_test.csv`; re-compare flags.
4. **Then** wire `pct_used` into `build_curve` so goals match CV-stage winsor — only after the escalations we keep look sensible.
5. Parallel CV levers if incremental-cap still leaves early Web/Blended flagged: early-patch `max_remove_fraction`, or accept flags + monitor (prior offline replay already showed greedy/A25 moves goals hard).
