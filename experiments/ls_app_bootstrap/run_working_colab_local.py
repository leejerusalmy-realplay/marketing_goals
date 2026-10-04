#!/usr/bin/env python3
"""Run the working LS App Colab locally (as_of 2026-08-19, App start 2026-08-05).

Executes helpers + RUN from:

    Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb

Skips Colab auth / Drive mount / browser download. Writes a new folder under
runs/. Does not change generic Combined, reference/, or DECISIONS.md.
"""
from __future__ import annotations

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

import run_goal120_realized as base  # noqa: E402

WORKING_NB = HERE / "Marketing_Goals_Combined_RP_LS_Colab_v2_winsor_esc_ls_app.ipynb"
CACHE = MG_ROOT / "experiments" / "cache" / "winsor_esc_ls_app_2026-08-19"
CREDS = PROJECT_ROOT / "oceanic-citadel-454608-d2-e116e15558ce.json"
RUNS = MG_ROOT / "runs"
MAIN_GOAL_COLS = [
    "brand",
    "population",
    "goal_horizon",
    "day",
    "raw_goal_ratio",
    "organic_share",
    "adjusted_goal_ratio",
]
EXPECTED_AS_OF = pd.Timestamp("2026-08-19").normalize()
EXPECTED_APP_START = pd.Timestamp("2026-08-05").normalize()


def log(msg: str) -> None:
    base.log(msg)


def notebook_code_cells(path: Path) -> list[tuple[int, str]]:
    import json

    nb = json.loads(path.read_text())
    out = []
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if src.strip():
            out.append((i, src))
    return out


def exec_helpers(ns: dict) -> None:
    """Load working-notebook helpers. Stop before RUN / EXPORT."""
    if not WORKING_NB.is_file():
        raise FileNotFoundError(f"Missing working Colab: {WORKING_NB}")
    log(f"helpers from {WORKING_NB.relative_to(MG_ROOT)}")
    for i, src in notebook_code_cells(WORKING_NB):
        head = "\n".join(src.splitlines()[:12])
        preview = src[:800]
        if "# RUN" in head or "UNIFIED RUN COMPLETE" in src:
            log(f"stop before Combined RUN cell ({i})")
            break
        if "# EXPORT" in head or "Run tag:" in src:
            log(f"stop before Combined EXPORT cell ({i})")
            break
        if "google.colab" in preview or "from google.colab" in src:
            log(f"skip Colab-only cell {i}")
            continue
        if "drive.mount" in src:
            log(f"skip Drive-mount cell {i}")
            continue
        log(f"exec Combined cell {i} ({len(src):,} chars)")
        exec(compile(src, f"{WORKING_NB.name}:cell_{i}", "exec"), ns, ns)


def confirm_experiment_knobs(ns: dict) -> None:
    as_of = pd.Timestamp(ns["AS_OF_DATE"]).normalize()
    app_start = pd.Timestamp(ns["LS_APP_START_DATE"]).normalize()
    ls_min = ns["BRAND_CONFIGS"]["lonestar"]["min_cohort_dates"]
    if as_of != EXPECTED_AS_OF:
        raise RuntimeError(f"AS_OF_DATE={as_of.date()} — expected {EXPECTED_AS_OF.date()}")
    if app_start != EXPECTED_APP_START:
        raise RuntimeError(
            f"LS_APP_START_DATE={app_start.date()} — expected {EXPECTED_APP_START.date()}"
        )
    if int(ls_min) != 20:
        raise RuntimeError(f"LS Web/Aff min_cohort_dates={ls_min} — expected 20")
    log(
        f"knobs ok  as_of={as_of.date()}  "
        f"ls_app_start={app_start.date()}  "
        f"ls_core_min_cohort_dates={ls_min}"
    )


def wrap_load_with_cache(ns: dict) -> None:
    orig_load = ns["load_brand_tables"]
    CACHE.mkdir(parents=True, exist_ok=True)

    def load_brand_tables(cfg, as_of_date=None):
        if as_of_date is None:
            as_of_date = ns["AS_OF_DATE"]
        brand = cfg["brand"]
        u_path = CACHE / f"{brand}_users.parquet"
        r_path = CACHE / f"{brand}_revenue.parquet"
        if u_path.exists() and r_path.exists():
            log(f"[{brand}] cache hit {CACHE.name}")
            return pd.read_parquet(u_path), pd.read_parquet(r_path)
        users_df, revenue_df = orig_load(cfg, as_of_date=as_of_date)
        users_df.to_parquet(u_path, index=False)
        revenue_df.to_parquet(r_path, index=False)
        log(f"[{brand}] cached users={len(users_df):,}  rev={len(revenue_df):,}")
        return users_df, revenue_df

    ns["load_brand_tables"] = load_brand_tables


def exec_run_cell(ns: dict) -> None:
    for i, src in notebook_code_cells(WORKING_NB):
        head = "\n".join(src.splitlines()[:12])
        if "# RUN" in head or "UNIFIED RUN COMPLETE" in src:
            log(f"exec Combined RUN cell {i} ({len(src):,} chars)")
            exec(compile(src, f"{WORKING_NB.name}:cell_{i}", "exec"), ns, ns)
            return
    raise RuntimeError(f"No RUN cell found in {WORKING_NB.name}")


def log_app_floor_check(ns: dict) -> None:
    ls_users = ns.get("ls_users")
    if ls_users is None or ls_users.empty:
        log("[lonestar] no ls_users in namespace after RUN")
        return
    users = ls_users.copy()
    users["cost_date"] = pd.to_datetime(users["cost_date"])
    app = users.loc[users["population"] == "App"]
    aff = users.loc[users["population"] == "Affiliate"]
    log(
        f"[lonestar] App users={len(app):,}  "
        f"dates={app['cost_date'].nunique() if not app.empty else 0}  "
        f"min={app['cost_date'].min().date() if not app.empty else None}  "
        f"max={app['cost_date'].max().date() if not app.empty else None}"
    )
    if not app.empty and app["cost_date"].min() < EXPECTED_APP_START:
        raise RuntimeError(
            f"App users exist before {EXPECTED_APP_START.date()} — floor did not apply"
        )
    pre_floor_aff = aff.loc[aff["cost_date"] < EXPECTED_APP_START]
    log(
        f"[lonestar] Affiliate users={len(aff):,}  "
        f"of which cost_date < {EXPECTED_APP_START.date()} = {len(pre_floor_aff):,}"
    )


def export_run(ns: dict) -> Path:
    as_of = pd.Timestamp(ns["AS_OF_DATE"]).date()
    exported_at = datetime.now()
    run_ts = exported_at.strftime("%H%M%S")
    run_tag = f"{as_of}_rp_ls_winsor_esc_ls_app_{run_ts}"
    out_dir = RUNS / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    goals_df = ns["goals_df"].copy()
    goals_detail_df = ns["goals_detail_df"].copy()
    curve_df = ns["curve_df"].copy()
    organic_df = ns["organic_df"].copy()
    cv_df = ns["cv_df"].copy()
    splice_day = ns["splice_day"]
    app_start = pd.Timestamp(ns["LS_APP_START_DATE"]).date()
    app_min = int(ns["ls_app_cfg"]["min_cohort_dates"])
    core_min = int(ns["ls_cfg"]["min_cohort_dates"])

    goals_df.to_csv(out_dir / "combined_goals.csv", index=False)
    goals_detail_df.to_csv(out_dir / "combined_goals_detail.csv", index=False)
    curve_df.to_csv(out_dir / "combined_arpu_curve.csv", index=False)
    organic_df.to_csv(out_dir / "combined_organic_share.csv", index=False)
    cv_df.to_csv(out_dir / "combined_cv_summary_adaptive_test.csv", index=False)

    pd.DataFrame(
        [
            dict(
                run_tag=run_tag,
                as_of_date=str(as_of),
                brands="realprize,lonestar",
                brand_slug="rp_ls",
                run_ts=run_ts,
                exported_at=exported_at.isoformat(timespec="seconds"),
                main_columns=",".join(MAIN_GOAL_COLS),
                env="local",
                engine="v2 winsor_esc + lonestar/App native_early_rp_tail",
                ls_app_winsor="0% locked (no escalation)",
                ls_app_organic="off (organic_share=0, adjusted=raw)",
                ls_blended_includes_app=False,
                ls_app_splice_day=splice_day,
                ls_app_start_date=str(app_start),
                ls_app_min_cohort_dates=app_min,
                ls_core_min_cohort_dates=core_min,
            )
        ]
    ).to_csv(out_dir / "run_meta.csv", index=False)

    (out_dir / "LABEL.md").write_text(
        "*Lee Jerusalmy*\n\n"
        "# Winsor escalation + LS App (App start 2026-08-05)\n\n"
        f"as_of **{as_of}**. Working Colab "
        f"`{WORKING_NB.name}` run locally. "
        "Other pops = capped winsor_esc. "
        f"lonestar/App = native through day {splice_day}, then RP App growth. "
        "App users counted only from **2026-08-05** (`affid=1` before that stays Affiliate). "
        f"LS App `min_cohort_dates = {app_min}` (temporary); Web/Aff stay {core_min}. "
        "LS App winsor locked at 0%. Organic off. Not a lock.\n"
    )
    log(f"exported {out_dir}")
    return out_dir


def main() -> int:
    if CREDS.is_file():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(CREDS))
        log(f"creds {CREDS.name}")
    else:
        raise FileNotFoundError(f"Missing BQ credentials: {CREDS}")

    ns: dict = {"__name__": "winsor_esc_ls_app_local"}
    exec_helpers(ns)
    confirm_experiment_knobs(ns)
    ns["MONITOR_STEPS"] = False
    wrap_load_with_cache(ns)
    log(
        f"as_of={ns['AS_OF_DATE'].date()}  "
        f"ls_app_start={ns['LS_APP_START_DATE'].date()}  "
        f"helpers={WORKING_NB.name}"
    )
    exec_run_cell(ns)
    log_app_floor_check(ns)
    out_dir = export_run(ns)
    print(out_dir)
    print(
        ns["goals_df"]
        .groupby(["brand", "population"], observed=True)
        .size()
        .rename("n_rows")
        .to_string()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
