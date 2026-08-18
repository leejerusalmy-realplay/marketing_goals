#!/usr/bin/env python3
"""Superseded. Use build_winsor_esc_plus_ls_app.py (do not run until Lee asks).

This older export used the cv_optimization winsor notebook and did not lock
LS App winsor at 0%. Keep only as a scratch copy.
"""
from __future__ import annotations

import copy
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
MG_ROOT = HERE.parents[1]
PROJECT_ROOT = MG_ROOT.parent
APRIL = MG_ROOT / "experiments" / "goal120_realized_2026-04-10"
sys.path.insert(0, str(APRIL))
sys.path.insert(0, str(HERE))

import run_goal120_realized as base  # noqa: E402
import run_goal120_winsor_esc as esc  # noqa: E402
import run_ls_app_bootstrap as boot  # noqa: E402

AS_OF = pd.Timestamp("2026-08-16").normalize()
CACHE = MG_ROOT / "experiments" / "cache" / "winsor_esc_plus_ls_app_2026-08-16"
CREDS = PROJECT_ROOT / "oceanic-citadel-454608-d2-e116e15558ce.json"
MAIN_GOAL_COLS = [
    "brand",
    "population",
    "goal_horizon",
    "day",
    "raw_goal_ratio",
    "organic_share",
    "adjusted_goal_ratio",
]


def log(msg: str) -> None:
    base.log(msg)


def enable_ls_app(ns: dict) -> None:
    cfg = ns["BRAND_CONFIGS"]["lonestar"]
    cfg["populations"] = ["Web", "App", "Affiliate"]
    trim = dict(cfg["trim_config"])
    trim["App"] = {"method": "winsor", "pct": 0}
    cfg["trim_config"] = trim
    orig_load = ns["load_brand_tables"]

    def load_brand_tables(cfg_in, as_of_date=None):
        if as_of_date is None:
            as_of_date = ns["AS_OF_DATE"]
        if cfg_in["brand"] != "lonestar":
            return orig_load(cfg_in, as_of_date=as_of_date)
        sql_floor = (
            as_of_date
            - pd.Timedelta(days=max(ns["GOAL_HORIZONS"]) + ns["LOOKBACK_COHORTS"] + 5)
        ).date()
        as_of = pd.Timestamp(as_of_date).date()
        log(f"[lonestar] SQL floor {sql_floor}  as_of={as_of}  (App enabled)")
        users = boot.read_gbq(ns, boot.ls_users_sql(cfg_in, sql_floor, as_of))
        rev = boot.read_gbq(ns, base.revenue_sql(cfg_in, sql_floor, as_of))
        users["cost_date"] = pd.to_datetime(users["cost_date"]).dt.date
        rev["date"] = pd.to_datetime(rev["date"]).dt.date
        return users, rev

    ns["load_brand_tables"] = load_brand_tables


def load_or_pull(ns: dict, brand_key: str, *, use_cache: bool):
    cfg = ns["BRAND_CONFIGS"][brand_key]
    brand = cfg["brand"]
    CACHE.mkdir(parents=True, exist_ok=True)
    u_path = CACHE / f"{brand}_users.parquet"
    r_path = CACHE / f"{brand}_revenue.parquet"
    if use_cache and u_path.exists() and r_path.exists():
        log(f"[{brand}] cache hit {CACHE.name}")
        return pd.read_parquet(u_path), pd.read_parquet(r_path)
    users_df, revenue_df = ns["load_brand_tables"](cfg, as_of_date=AS_OF)
    users_df.to_parquet(u_path, index=False)
    revenue_df.to_parquet(r_path, index=False)
    log(f"[{brand}] cached users={len(users_df):,}  rev={len(revenue_df):,}")
    return users_df, revenue_df


def stamp_source(df: pd.DataFrame, source: str) -> pd.DataFrame:
    out = df.copy()
    out["engine_source"] = source
    return out


def main() -> int:
    if CREDS.is_file():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(CREDS))

    ns: dict = {"__name__": "winsor_plus_ls_app"}
    base.exec_combined_helpers(ns, nb_path=esc.WINSOR_NB)
    esc.confirm_capped_engine(ns)
    esc.wire_pct_used_into_curve(ns)
    ns["AS_OF_DATE"] = AS_OF
    ns["MONITOR_STEPS"] = False
    enable_ls_app(ns)
    log(f"as_of={AS_OF.date()}  horizons={ns['GOAL_HORIZONS']}")

    rp_users, rp_rev = load_or_pull(ns, "realprize", use_cache=True)
    ls_users, ls_rev = load_or_pull(ns, "lonestar", use_cache=True)

    rp_cfg = copy.deepcopy(ns["BRAND_CONFIGS"]["realprize"])
    ls_cfg = copy.deepcopy(ns["BRAND_CONFIGS"]["lonestar"])
    ls_core_cfg = copy.deepcopy(ls_cfg)
    ls_core_cfg["populations"] = ["Web", "Affiliate"]
    ls_app_cfg = copy.deepcopy(ls_cfg)
    ls_app_cfg["populations"] = ["App"]

    log("[realprize] winsor_esc full")
    ns.get("_pct_used_by_pop_e", {}).clear()
    rp_res = ns["run_brand_pipeline"](rp_cfg, rp_users, rp_rev, as_of_date=AS_OF, monitor=False)

    log("[lonestar] winsor_esc Web + Affiliate + Blended (no App in Blended)")
    ns.get("_pct_used_by_pop_e", {}).clear()
    ls_core = ns["run_brand_pipeline"](
        ls_core_cfg, ls_users, ls_rev, as_of_date=AS_OF, monitor=False
    )

    log("[lonestar] App native (winsor_esc), then RP App tail")
    ns.get("_pct_used_by_pop_e", {}).clear()
    ls_app_native = ns["run_brand_pipeline"](
        ls_app_cfg, ls_users, ls_rev, as_of_date=AS_OF, monitor=False
    )

    max_day = max(ns["GOAL_HORIZONS"])
    spliced, splice_day = boot.native_early_rp_tail_curve(
        ls_app_native["curve"],
        rp_res["curve"],
        max_day=max_day,
    )
    ns["apply_brand_globals"](ls_cfg)
    app_goals = ns["build_goals"](
        spliced,
        ls_core["organic"],
        ["App"],
        goal_horizons=ns["GOAL_HORIZONS"],
        organic_share_cap_horizon=ns.get("ORGANIC_SHARE_CAP_HORIZON"),
    )
    app_goals.insert(0, "brand", "lonestar")
    log(f"[lonestar/App] spliced goals rows={len(app_goals):,}  splice_day={splice_day}")

    rp_goals = stamp_source(rp_res["goals"], "winsor_esc")
    ls_goals = stamp_source(ls_core["goals"], "winsor_esc")
    app_goals = stamp_source(app_goals, "native_early_rp_tail")

    goals_detail = pd.concat([rp_goals, ls_goals, app_goals], ignore_index=True)
    goals_detail = goals_detail.sort_values(
        ["brand", "population", "goal_horizon", "day"]
    ).reset_index(drop=True)
    goals_main = goals_detail[MAIN_GOAL_COLS].copy()

    rp_curve = stamp_source(rp_res["curve"], "winsor_esc")
    ls_curve = stamp_source(ls_core["curve"], "winsor_esc")
    app_curve = spliced.copy()
    if "brand" not in app_curve.columns:
        app_curve.insert(0, "brand", "lonestar")
    else:
        app_curve["brand"] = "lonestar"
    app_curve = stamp_source(app_curve, "native_early_rp_tail")
    curve_df = pd.concat([rp_curve, ls_curve, app_curve], ignore_index=True)

    organic_df = pd.concat([rp_res["organic"], ls_core["organic"]], ignore_index=True)
    cv_df = pd.concat(
        [rp_res["cv"], ls_core["cv"], ls_app_native["cv"]], ignore_index=True
    )
    if not cv_df.empty:
        cv_df = stamp_source(cv_df, "winsor_esc")

    run_ts = datetime.now().strftime("%H%M%S")
    out_dir = MG_ROOT / "runs" / f"2026-08-16_rp_ls_winsor_esc_plus_ls_app_{run_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    goals_main.to_csv(out_dir / "combined_goals.csv", index=False)
    goals_detail.to_csv(out_dir / "combined_goals_detail.csv", index=False)
    curve_df.to_csv(out_dir / "combined_arpu_curve.csv", index=False)
    organic_df.to_csv(out_dir / "combined_organic_share.csv", index=False)
    cv_df.to_csv(out_dir / "combined_cv_summary.csv", index=False)

    counts = (
        goals_main.groupby(["brand", "population"], observed=True)
        .size()
        .rename("n_rows")
        .reset_index()
    )
    counts.to_csv(out_dir / "row_counts.csv", index=False)

    pd.DataFrame(
        [
            dict(
                as_of_date=str(AS_OF.date()),
                engine="winsor_esc + lonestar/App native_early_rp_tail",
                ls_app_splice_day=splice_day,
                pct_used_wired_into_curve=True,
                ls_blended_includes_app=False,
                run_ts=run_ts,
                exported_at=datetime.now().isoformat(timespec="seconds"),
            )
        ]
    ).to_csv(out_dir / "run_meta.csv", index=False)

    label = (
        "*Lee Jerusalmy*\n\n"
        "# Winsor escalation + LS App bootstrap\n\n"
        f"as_of **{AS_OF.date()}**. "
        "All populations = capped winsor_escalation (`pct_used` wired). "
        "lonestar/App = `native_early_rp_tail` (native through last measured day, "
        f"then RP App growth; splice after day {splice_day}). "
        "LS Blended does **not** include App. Provisional — not a methodology lock.\n"
    )
    (out_dir / "LABEL.md").write_text(label)

    writeup = [
        "*Lee Jerusalmy*",
        "",
        "# Combined goals — winsor_esc + LS App native_early_rp_tail",
        "",
        f"as_of **{AS_OF.date()}**.",
        "",
        "- **RP all pops + LS Web / Affiliate / Blended:** capped winsor_escalation.",
        f"- **LS App:** native through day **{splice_day}**, then RP App day-growth.",
        "- LS Blended stays Web+Affiliate only (App is an add-on, not folded in).",
        "",
        "Main file: `combined_goals.csv` "
        "(brand, population, goal_horizon, day, raw_goal_ratio, organic_share, adjusted_goal_ratio).",
        "",
        "Not a methodology lock.",
        "",
        "## Row counts",
        "",
        counts.to_string(index=False),
        "",
    ]
    (out_dir / "WRITEUP.md").write_text("\n".join(writeup))

    print(counts.to_string(index=False))
    log(f"exported {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
