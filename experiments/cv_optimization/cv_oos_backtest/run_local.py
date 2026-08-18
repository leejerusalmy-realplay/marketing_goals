#!/usr/bin/env python3
"""Local walk-forward runner for cv_oos_backtest.

Executes the experiment notebook helpers with service-account auth,
caches the widened BQ extract, and skips unused day-step curve rebuilds
(framework only — same patch_cv_adaptive / mean_after / min_cohort_dates).
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROJECT_ROOT = ROOT.parent
NB_PATH = HERE / "Marketing_Goals_Combined_RP_LS_Colab.ipynb"
CACHE = ROOT / "experiments" / "cache" / "cv_oos_backtest_2026-08-03"
CREDS = PROJECT_ROOT / "oceanic-citadel-454608-d2-e116e15558ce.json"
RUNS = ROOT / "runs"
LOG = HERE / "run_local.log"


def log(msg: str) -> None:
    line = f"{datetime.now().strftime('%H:%M:%S')}  {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def cell_src(nb, i: int) -> str:
    return "".join(nb["cells"][i].get("source", []))


def exec_cell(ns: dict, src: str, label: str) -> None:
    log(f"exec {label} ({len(src):,} chars)")
    exec(compile(src, label, "exec"), ns, ns)


def wrap_load_with_cache(ns: dict) -> None:
    orig = ns["load_brand_tables"]
    CACHE.mkdir(parents=True, exist_ok=True)

    def load_brand_tables(cfg, as_of_date=None):
        if as_of_date is None:
            as_of_date = ns["AS_OF_DATE"]
        brand = cfg["brand"]
        u_path = CACHE / f"{brand}_users.parquet"
        r_path = CACHE / f"{brand}_revenue.parquet"
        if u_path.exists() and r_path.exists():
            log(f"[{brand}] cache hit {CACHE}")
            import pandas as pd

            return pd.read_parquet(u_path), pd.read_parquet(r_path)
        log(f"[{brand}] BQ pull (widened floor) → cache")
        users_df, revenue_df = orig(cfg, as_of_date=as_of_date)
        users_df.to_parquet(u_path, index=False)
        revenue_df.to_parquet(r_path, index=False)
        log(f"[{brand}] cached users={len(users_df):,} rev={len(revenue_df):,}")
        return users_df, revenue_df

    ns["load_brand_tables"] = load_brand_tables


def install_fast_walkforward(ns: dict) -> None:
    """Replace run_walkforward_backtest: CV first-pass only + growth cache."""
    import numpy as np
    import pandas as pd

    def collect_patch_cv_at_T(u_base, daily, *, populations, as_of_date, debug=False):
        rows = []
        patch_cv_adaptive = ns["patch_cv_adaptive"]
        PATCHES = ns["PATCHES"]
        for pop in populations:
            u_p = u_base.loc[u_base["population"] == pop]
            d_p = daily.loc[daily["population"] == pop]
            excluded_uids = set()
            for s, e in PATCHES:
                _patch, stats, _removed, _flagged, newly_excluded = patch_cv_adaptive(
                    u_p,
                    d_p,
                    population=pop,
                    s=s,
                    e=e,
                    as_of_date=as_of_date,
                    excluded_uids=excluded_uids,
                    debug=debug,
                )
                excluded_uids |= newly_excluded
                if not stats:
                    continue
                min_cohort_dates = ns.get("MIN_COHORT_DATES", 1)
                if stats.get("n_cohort_dates_total", 0) < min_cohort_dates:
                    continue
                rows.append(stats)
        return pd.DataFrame(rows)

    def run_walkforward_backtest(
        brand_key,
        users_df,
        revenue_df,
        *,
        cutoff_dates,
        eval_as_of,
        test_horizons,
        debug=False,
    ):
        BRAND_CONFIGS = ns["BRAND_CONFIGS"]
        apply_brand_globals = ns["apply_brand_globals"]
        build_user_revenue_cums = ns["build_user_revenue_cums"]
        list_candidate_test_dates = ns["list_candidate_test_dates"]
        growth_for_cost_date = ns["growth_for_cost_date"]
        summarize_errors = ns["summarize_errors"]
        APE_NEAR_ZERO_GOAL = ns["APE_NEAR_ZERO_GOAL"]

        cfg = BRAND_CONFIGS[brand_key]
        apply_brand_globals(cfg)
        brand = cfg["brand"]
        rows = []
        point_rows = []
        growth_cache = {}

        def cached_growth(u_base, daily, *, population, s, e, cost_date):
            key = (population, int(s), int(e), str(cost_date))
            if key not in growth_cache:
                growth_cache[key] = growth_for_cost_date(
                    u_base, daily, population=population, s=s, e=e, cost_date=cost_date
                )
            return growth_cache[key]

        pops = list(cfg["populations"])
        log(f"[{brand}] building user cums (pops={pops})...")
        u_pop, daily_pop = build_user_revenue_cums(
            users_df.loc[users_df["population"].isin(pops)].copy(),
            revenue_df,
            max_day=365,
        )
        log(f"[{brand}] pop cums: users={len(u_pop):,} daily_rows={len(daily_pop):,}")
        users_blend = users_df.copy()
        users_blend["population"] = "Blended"
        log(f"[{brand}] building blended cums...")
        u_blend, daily_blend = build_user_revenue_cums(users_blend, revenue_df, max_day=365)
        log(f"[{brand}] blend cums: users={len(u_blend):,} daily_rows={len(daily_blend):,}")

        n_cut = len(cutoff_dates)
        for i_t, T in enumerate(cutoff_dates, start=1):
            T = pd.Timestamp(T).normalize()
            log(f"[{brand}] cutoff {i_t}/{n_cut} as_of={T.date()}")
            cv_pop = collect_patch_cv_at_T(
                u_pop,
                daily_pop,
                populations=list(cfg["populations"]),
                as_of_date=T,
                debug=debug,
            )
            cv_blend = collect_patch_cv_at_T(
                u_blend,
                daily_blend,
                populations=["Blended"],
                as_of_date=T,
                debug=debug,
            )
            cv_t = pd.concat(
                [x for x in [cv_pop, cv_blend] if x is not None and not x.empty],
                ignore_index=True,
            )
            if cv_t.empty:
                log(f"  [{brand}] no patches at {T.date()}")
                continue
            log(f"  [{brand}] patches={len(cv_t)}  scoring OOS...")

            for _, st in cv_t.iterrows():
                pop = st["population"]
                patch = st["patch"]
                s, e = map(int, patch.split("->"))
                goal = st.get("mean_after")
                training_start = st.get("cohort_start")
                training_end = st.get("cohort_end")
                u_base = u_blend if pop == "Blended" else u_pop
                daily = daily_blend if pop == "Blended" else daily_pop

                for h in test_horizons:
                    test_dates = list_candidate_test_dates(
                        u_base,
                        population=pop,
                        training_end=training_end,
                        n_wanted=h,
                        e=e,
                        eval_as_of=eval_as_of,
                    )
                    actuals = []
                    for d in test_dates:
                        g = cached_growth(
                            u_base, daily, population=pop, s=s, e=e, cost_date=d
                        )
                        if g is None:
                            continue
                        actuals.append(g["actual_growth"])
                        if goal is not None and np.isfinite(goal):
                            ae = abs(g["actual_growth"] - float(goal))
                            ape = (
                                (ae / abs(float(goal)))
                                if abs(float(goal)) > APE_NEAR_ZERO_GOAL
                                else np.nan
                            )
                            point_rows.append(
                                {
                                    "brand": brand,
                                    "population": pop,
                                    "patch": patch,
                                    "cutoff_as_of": str(T.date()),
                                    "training_start": training_start,
                                    "training_end": training_end,
                                    "goal": float(goal)
                                    if goal is not None and np.isfinite(goal)
                                    else None,
                                    "cv_after": st.get("cv_after"),
                                    "flagged": st.get("flagged"),
                                    "test_horizon": int(h),
                                    "test_cost_date": str(g["cost_date"]),
                                    "actual_growth": g["actual_growth"],
                                    "abs_error": ae,
                                    "ape": ape if np.isfinite(ape) else None,
                                    "signed_error": g["actual_growth"] - float(goal),
                                    "n_test_users": g["n_users"],
                                }
                            )

                    err = ns["summarize_errors"](actuals, goal)
                    rows.append(
                        {
                            "brand": brand,
                            "population": pop,
                            "patch": patch,
                            "cutoff_as_of": str(T.date()),
                            "training_start": training_start,
                            "training_end": training_end,
                            "n_training_cohorts": st.get("n_cohort_dates_total"),
                            "n_training_cohorts_kept": st.get("n_cohort_dates_kept"),
                            "n_training_users": st.get("n_users_post_trim"),
                            "goal": float(goal)
                            if goal is not None
                            and np.isfinite(float(goal) if goal is not None else np.nan)
                            else None,
                            "cv_before": st.get("cv_before"),
                            "cv_after": st.get("cv_after"),
                            "flagged_using_existing_logic": bool(st.get("flagged")),
                            "cv_threshold_used": float(ns["CV_THRESHOLD"]),
                            "test_horizon": int(h),
                            "n_test_dates_available": len(test_dates),
                            "insufficient_test_data": len(actuals) < int(h),
                            **err,
                        }
                    )

        log(f"[{brand}] growth cache size={len(growth_cache):,}")
        return pd.DataFrame(rows), pd.DataFrame(point_rows)

    ns["collect_patch_cv_at_T"] = collect_patch_cv_at_T
    ns["run_walkforward_backtest"] = run_walkforward_backtest
    log("Installed CV-only walk-forward (no day-step curve rebuild).")


def write_label(out_dir: Path) -> None:
    (out_dir / "LABEL.md").write_text(
        "*Lee Jerusalmy*\n\n"
        "# CV → OOS walk-forward backtest\n\n"
        "Does in-sample `cv_after` predict out-of-sample patch-goal error "
        "(`mean_after` vs later cohort growth)? "
        "Biweekly cutoffs, 180d span, primary horizon 14. "
        "Production knobs unchanged. Winsor escalation still parked.\n"
    )


def main() -> int:
    LOG.write_text("")
    log("=== cv_oos_backtest local run start ===")
    if not CREDS.is_file():
        log(f"MISSING creds: {CREDS}")
        return 1
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDS)
    log(f"Using creds {CREDS.name}")

    nb = json.loads(NB_PATH.read_text())
    ns = {
        "__name__": "__main__",
        "project_id": "oceanic-citadel-454608-d2",
    }

    # Config + helpers (skip Colab auth / Drive mount)
    for i in (4, 5, 6, 7, 8, 9, 10, 11):
        exec_cell(ns, cell_src(nb, i), f"cell_{i}")

    ns["MONITOR_STEPS"] = False
    wrap_load_with_cache(ns)
    install_fast_walkforward(ns)

    exec_cell(ns, cell_src(nb, 12), "cell_12_walkforward")
    exec_cell(ns, cell_src(nb, 13), "cell_13_analysis")
    exec_cell(ns, cell_src(nb, 14), "cell_14_final")
    exec_cell(ns, cell_src(nb, 15), "cell_15_export")

    # LABEL.md on the Drive export if it landed
    run_tag = ns.get("run_tag")
    if run_tag:
        out_dir = RUNS / run_tag
        if out_dir.is_dir():
            write_label(out_dir)
            log(f"LABEL.md written → {out_dir}")
        else:
            log(f"run_tag={run_tag} but folder missing")
    log("=== cv_oos_backtest local run done ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log(traceback.format_exc())
        raise
