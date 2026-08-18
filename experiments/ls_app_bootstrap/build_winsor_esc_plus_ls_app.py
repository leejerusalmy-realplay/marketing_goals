#!/usr/bin/env python3
"""Combined goals file: capped winsor_escalation + lonestar/App native_early_rp_tail.

Do not run until Lee asks. Does not change generic Combined or DECISIONS.md.

Base engine
-----------
Helpers from Lee's current Combined freeze:

    notebooks/versions/v2_2026-08_winsor_escalation_combined/
      Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc.ipynb

Capped winsor_esc: escalate toward cv_threshold; stop if revenue cut > 15%.
`pct_used` is wired into the curve at runtime (the archived notebook still
builds day-steps on the config-floor winsor).

What each cell gets
-------------------
RP all pops + LS Web / Affiliate / Blended:
    capped winsor_esc.

LS App (add-on; not folded into LS Blended):
    1. Map affid = 1 → population App, with RP-style scope/bucket
       (app vs non_app; App organic = channel_type app_organic).
    2. Same boxes as other pops through last *measured* patch.
    3. Winsor floor 0% and stays 0% — no escalation ladder on LS App.
    4. Growth + CV + day-steps on measured patches; D1 = LS App own
       pooled day-1 ARPU (native pass, before the RP tail).
    5. Keep native curve through last non-extrapolated day S.
    6. After S, do **not** use LS tail extrapolation. Stick RP App
       day-growth from the RP winsor_esc curve in this same run:

           ARPU(d) = ARPU(d-1) × (ARPU_RP_App(d) / ARPU_RP_App(d-1))

    7. Goals: raw = ARPU(d)/ARPU(H). Organic = RP-style scope (App uses
       `app`, Web/Aff use `non_app`). Blended organic = 0.

Run later (not now):
  python experiments/ls_app_bootstrap/build_winsor_esc_plus_ls_app.py
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
V2_NB = (
    MG_ROOT
    / "notebooks"
    / "versions"
    / "v2_2026-08_winsor_escalation_combined"
    / "Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc.ipynb"
)
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


def enable_ls_app_map(ns: dict) -> None:
    """Map affid=1 → App. Do not add App into LS Blended."""
    cfg = ns["BRAND_CONFIGS"]["lonestar"]
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
        log(f"[lonestar] SQL floor {sql_floor}  as_of={as_of}  (App mapped)")
        users = boot.read_gbq(ns, boot.ls_users_sql(cfg_in, sql_floor, as_of))
        rev = boot.read_gbq(ns, base.revenue_sql(cfg_in, sql_floor, as_of))
        users["cost_date"] = pd.to_datetime(users["cost_date"]).dt.date
        rev["date"] = pd.to_datetime(rev["date"]).dt.date
        return users, rev

    ns["load_brand_tables"] = load_brand_tables


def lock_app_winsor_floor(ns: dict) -> None:
    """LS App stays at 0% winsor — no escalation ladder on this population."""
    orig_patch = ns["patch_cv_adaptive"]

    def patch_cv_adaptive(*args, **kwargs):
        population = kwargs.get("population")
        if population is None and args:
            population = args[2] if len(args) > 2 else None
        if population == "App" and ns.get("BRAND") == "lonestar":
            kwargs = dict(kwargs)
            kwargs["pct_override"] = 0.0
        return orig_patch(*args, **kwargs)

    ns["patch_cv_adaptive"] = patch_cv_adaptive


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
    if not V2_NB.is_file():
        raise FileNotFoundError(f"Missing v2 winsor_esc notebook: {V2_NB}")
    if CREDS.is_file():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(CREDS))

    ns: dict = {"__name__": "winsor_esc_plus_ls_app"}
    base.exec_combined_helpers(ns, nb_path=V2_NB)
    esc.confirm_capped_engine(ns)
    esc.wire_pct_used_into_curve(ns)
    ns["AS_OF_DATE"] = AS_OF
    ns["MONITOR_STEPS"] = False
    enable_ls_app_map(ns)
    lock_app_winsor_floor(ns)
    log(f"as_of={AS_OF.date()}  horizons={ns['GOAL_HORIZONS']}  helpers={V2_NB.name}")

    rp_users, rp_rev = load_or_pull(ns, "realprize", use_cache=True)
    ls_users, ls_rev = load_or_pull(ns, "lonestar", use_cache=True)

    rp_cfg = copy.deepcopy(ns["BRAND_CONFIGS"]["realprize"])
    ls_cfg = copy.deepcopy(ns["BRAND_CONFIGS"]["lonestar"])
    ls_core_cfg = copy.deepcopy(ls_cfg)
    ls_core_cfg["populations"] = ["Web", "Affiliate"]
    ls_app_cfg = copy.deepcopy(ls_cfg)
    ls_app_cfg["populations"] = ["App"]

    log("[realprize] capped winsor_esc (all pops)")
    ns.get("_pct_used_by_pop_e", {}).clear()
    rp_res = ns["run_brand_pipeline"](
        rp_cfg, rp_users, rp_rev, as_of_date=AS_OF, monitor=False
    )

    log("[lonestar] capped winsor_esc Web + Affiliate + Blended (no App)")
    ns.get("_pct_used_by_pop_e", {}).clear()
    ls_core = ns["run_brand_pipeline"](
        ls_core_cfg, ls_users, ls_rev, as_of_date=AS_OF, monitor=False
    )

    log("[lonestar/App] native measured patches (winsor 0%), then RP App tail")
    ns.get("_pct_used_by_pop_e", {}).clear()
    ns["BRAND"] = "lonestar"
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
        organic_share_cap_horizon=None,
    )
    if "brand" not in app_goals.columns:
        app_goals.insert(0, "brand", "lonestar")
    else:
        app_goals["brand"] = "lonestar"
    # Provisional: no App organic haircut until App has enough horizon history.
    app_goals["organic_share"] = 0.0
    app_goals["adjusted_goal_ratio"] = app_goals["raw_goal_ratio"]
    log(f"[lonestar/App] splice_day={splice_day}  goals={len(app_goals):,}")

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

    pd.DataFrame(
        [
            dict(
                as_of_date=str(AS_OF.date()),
                helpers=str(V2_NB.relative_to(MG_ROOT)),
                ls_app_method="native_early_rp_tail",
                ls_app_mapping="affid=1 → App + RP-style scope/bucket",
                ls_app_winsor="0% locked (no escalation)",
                ls_app_splice_day=splice_day,
                ls_app_organic="off (organic_share=0, adjusted=raw)",
                ls_blended_includes_app=False,
                other_pops="capped winsor_esc, pct_used wired",
                run_ts=run_ts,
                exported_at=datetime.now().isoformat(timespec="seconds"),
            )
        ]
    ).to_csv(out_dir / "run_meta.csv", index=False)

    (out_dir / "LABEL.md").write_text(
        "*Lee Jerusalmy*\n\n"
        "# Winsor escalation + LS App native_early_rp_tail\n\n"
        f"as_of **{AS_OF.date()}**. Helpers from `{V2_NB.name}`. "
        "Other pops = capped winsor_esc. "
        f"lonestar/App = native through day {splice_day}, then RP App growth. "
        "LS App winsor locked at 0%. LS Blended excludes App. Not a lock.\n"
    )
    log(f"exported {out_dir}")
    print(goals_main.groupby(["brand", "population"]).size().rename("n_rows").to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
