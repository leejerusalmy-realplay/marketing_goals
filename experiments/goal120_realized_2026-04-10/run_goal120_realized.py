#!/usr/bin/env python3
"""Freeze Combined at 2026-04-10 and score horizon-120 daily goals vs Apr 10–14 actuals.

Uses generic Combined helpers (notebooks/Marketing_Goals_Combined_RP_LS.ipynb).
Does not change production knobs. Does not write into generic notebooks.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MG_ROOT = HERE.parents[1]
PROJECT_ROOT = MG_ROOT.parent
COMBINED_NB = MG_ROOT / "notebooks" / "Marketing_Goals_Combined_RP_LS.ipynb"
CACHE = MG_ROOT / "experiments" / "cache" / "goal120_realized_2026-04-10"
RUNS = MG_ROOT / "runs"
CREDS = PROJECT_ROOT / "oceanic-citadel-454608-d2-e116e15558ce.json"

# ── Locked check knobs (not production Combined defaults) ──
FREEZE_AS_OF = pd.Timestamp("2026-04-10").normalize()
EVAL_START = pd.Timestamp("2026-04-10").normalize()
EVAL_END = pd.Timestamp("2026-04-14").normalize()
GOAL_HORIZON = 120
LOOKBACK_COHORTS = 35
NARROW_PATCHES = (
    (1, 7),
    (7, 14),
    (14, 30),
    (30, 60),
    (60, 90),
    (90, 120),
)
MILESTONE_DAYS = (1, 7, 30, 60, 90, 120)
# Last deposit needed for Apr 14 day 120: cost_date + 119
EVAL_DEPOSIT_END = EVAL_END + pd.Timedelta(days=GOAL_HORIZON - 1)
SQL_FLOOR = (
    FREEZE_AS_OF - pd.Timedelta(days=GOAL_HORIZON + LOOKBACK_COHORTS + 5)
).normalize()
APE_NEAR_ZERO = 1e-8


def log(msg: str) -> None:
    print(f"{datetime.now().strftime('%H:%M:%S')}  {msg}", flush=True)


def exec_combined_helpers(ns: dict, nb_path: Path | None = None) -> None:
    """Load Combined auth + helpers. Stop before the generic RUN cell."""
    path = Path(nb_path) if nb_path is not None else COMBINED_NB
    if not path.is_file():
        raise FileNotFoundError(f"Combined notebook not found: {path}")
    try:
        import google.colab  # noqa: F401

        in_colab = True
    except ImportError:
        in_colab = False
    nb = json.loads(path.read_text())
    log(f"helpers from {path.relative_to(MG_ROOT) if path.is_relative_to(MG_ROOT) else path}")
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if not src.strip():
            continue
        head = "\n".join(src.splitlines()[:12])
        preview = src[:800]
        # Combined RUN cell starts with a banner, then "# RUN — both brands"
        if (
            "# RUN" in head
            or "UNIFIED RUN COMPLETE" in src
            or "Run tag:" in src
            or (
                "load_brand_tables" in src
                and "for brand_key in RUN_BRANDS" in src
            )
        ):
            log(f"stop before Combined RUN/export cell ({i})")
            break
        if not in_colab and ("google.colab" in preview or "from google.colab" in src):
            log(f"skip Colab-only cell {i}")
            continue
        if "drive.mount" in src:
            log(f"skip Drive-mount cell {i}")
            continue
        log(f"exec Combined cell {i} ({len(src):,} chars)")
        exec(compile(src, f"{path.name}:cell_{i}", "exec"), ns, ns)


def apply_check_calendar(ns: dict) -> None:
    """Pin freeze date + H=120-only patches. Brand knobs stay Combined as-is."""
    ns["AS_OF_DATE"] = FREEZE_AS_OF
    ns["PATCHES"] = NARROW_PATCHES
    ns["GOAL_HORIZONS"] = [GOAL_HORIZON]
    ns["CHECKPOINTS"] = [GOAL_HORIZON]
    ns["LOOKBACK_COHORTS"] = LOOKBACK_COHORTS
    ns["MONITOR_STEPS"] = False
    ns["MONITOR_PREVIEW_DAYS"] = list(MILESTONE_DAYS)
    ns["MONITOR_PREVIEW_HORIZONS"] = [GOAL_HORIZON]
    log(
        f"calendar: as_of={FREEZE_AS_OF.date()}  "
        f"patches={list(NARROW_PATCHES)}  horizon={GOAL_HORIZON}"
    )


def users_sql(cfg: dict, cost_start, cost_end) -> str:
    """Same Combined population map; bounded cost_date window."""
    brand = cfg["brand"]
    cost_table = cfg["cost_table"]
    excl_sql = ", ".join(str(a) for a in cfg["exclude_affids"])
    start = pd.Timestamp(cost_start).date()
    end = pd.Timestamp(cost_end).date()
    if brand == "realprize":
        return f"""
        SELECT
          id,
          CASE
            WHEN affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069) THEN 'Web'
            WHEN affid = 1                                    THEN 'App'
            WHEN affid IN (64, 71)                            THEN 'PPC'
            WHEN affid IN (0, 78, 2290)                       THEN 'Organic'
            ELSE 'Affiliate'
          END AS population,
          CASE WHEN affid = 1 THEN 'app' ELSE 'non_app' END AS scope,
          CASE
            WHEN affid = 1 AND channel_type = 'app_organic' THEN 'organic'
            WHEN affid = 1                                   THEN 'acquired'
            WHEN affid IN (0, 78, 2290)                      THEN 'organic'
            ELSE 'acquired'
          END AS bucket,
          DATE(MIN(cost_date)) AS cost_date
        FROM `{cost_table}`
        WHERE cost_date >= DATE('{start}')
          AND cost_date <= DATE('{end}')
          AND affid NOT IN ({excl_sql})
          AND id > 0
        GROUP BY id, population, scope, bucket
        """
    if brand == "lonestar":
        return f"""
        SELECT
          id,
          CASE
            WHEN affid IN (63, 4432, 4551, 4698, 5048, 5125, 7120, 7253, 7260, 8331, 8345) THEN 'Web'
            WHEN affid IN (64, 71)  THEN 'PPC'
            WHEN affid IN (0, 78)   THEN 'Organic'
            ELSE 'Affiliate'
          END AS population,
          DATE(MIN(cost_date)) AS cost_date
        FROM `{cost_table}`
        WHERE cost_date >= DATE('{start}')
          AND cost_date <= DATE('{end}')
          AND affid NOT IN ({excl_sql})
          AND id > 0
        GROUP BY 1, 2
        """
    raise ValueError(f"Unknown brand: {brand}")


def revenue_sql(cfg: dict, date_start, date_end) -> str:
    dep_table = cfg["deposits_table"]
    start = pd.Timestamp(date_start).date()
    end = pd.Timestamp(date_end).date()
    return f"""
    SELECT
      playerId AS playerid,
      DATE(date) AS date,
      SUM(amount) / 100.0 AS amount
    FROM `{dep_table}`
    WHERE Status = 'APPROVED'
      AND date >= DATE('{start}')
      AND date <= DATE('{end}')
    GROUP BY 1, 2
    """


def read_gbq(ns: dict, sql: str):
    return ns["read_gbq"](sql, project_id=ns["project_id"], use_bqstorage_api=True)


def count_eval_users(ns: dict) -> pd.DataFrame:
    """Cheap volume check — eval cost_dates only, no deposits."""
    rows = []
    for brand_key in ns["RUN_BRANDS"]:
        cfg = ns["BRAND_CONFIGS"][brand_key]
        sql = f"""
        SELECT
          '{cfg["brand"]}' AS brand,
          population,
          cost_date,
          COUNT(*) AS n_users
        FROM (
          {users_sql(cfg, EVAL_START, EVAL_END)}
        )
        GROUP BY population, cost_date
        ORDER BY population, cost_date
        """
        log(f"[{cfg['brand']}] count-only eval users")
        part = read_gbq(ns, sql)
        rows.append(part)
    out = pd.concat(rows, ignore_index=True)
    out["cost_date"] = pd.to_datetime(out["cost_date"]).dt.date
    return out


def load_narrow_tables(ns: dict, cfg: dict, *, use_cache: bool):
    """One bounded pull: training floor → eval end (users), deposits through day 120 of Apr 14."""
    brand = cfg["brand"]
    CACHE.mkdir(parents=True, exist_ok=True)
    u_path = CACHE / f"{brand}_users.parquet"
    r_path = CACHE / f"{brand}_revenue.parquet"
    if use_cache and u_path.exists() and r_path.exists():
        log(f"[{brand}] cache hit {CACHE.name}")
        return pd.read_parquet(u_path), pd.read_parquet(r_path)

    log(
        f"[{brand}] BQ pull  users {SQL_FLOOR.date()}→{EVAL_END.date()}  "
        f"deposits {SQL_FLOOR.date()}→{EVAL_DEPOSIT_END.date()}"
    )
    users_df = read_gbq(ns, users_sql(cfg, SQL_FLOOR, EVAL_END))
    revenue_df = read_gbq(ns, revenue_sql(cfg, SQL_FLOOR, EVAL_DEPOSIT_END))
    users_df["cost_date"] = pd.to_datetime(users_df["cost_date"]).dt.date
    revenue_df["date"] = pd.to_datetime(revenue_df["date"]).dt.date
    users_df.to_parquet(u_path, index=False)
    revenue_df.to_parquet(r_path, index=False)
    log(f"[{brand}] cached users={len(users_df):,}  rev={len(revenue_df):,}")
    return users_df, revenue_df


def split_train_eval(users_df, revenue_df):
    """Training: information available at T. Eval: Apr 10–14 + realized deposits."""
    freeze = FREEZE_AS_OF.date()
    eval_dates = set(pd.date_range(EVAL_START, EVAL_END, freq="D").date)
    u = users_df.copy()
    r = revenue_df.copy()
    u["cost_date"] = pd.to_datetime(u["cost_date"]).dt.date
    r["date"] = pd.to_datetime(r["date"]).dt.date

    train_users = u.loc[u["cost_date"] < freeze].copy()
    train_rev = r.loc[r["date"] < freeze].copy()
    eval_users = u.loc[u["cost_date"].isin(eval_dates)].copy()
    eval_rev = r.copy()
    return train_users, train_rev, eval_users, eval_rev


def run_frozen_goals(ns: dict, brand_key: str, train_users, train_rev) -> dict:
    cfg = ns["BRAND_CONFIGS"][brand_key]
    log(f"[{cfg['brand']}] Combined pipeline as_of={FREEZE_AS_OF.date()}")
    return ns["run_brand_pipeline"](
        cfg,
        train_users,
        train_rev,
        as_of_date=FREEZE_AS_OF,
        monitor=False,
    )


def _norm_cost(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.date


def realized_arpu_path(ns, users_slice, revenue_df, *, population: str, max_day: int = 120):
    """Raw realized ARPU path. No winsor. Day D uses dsi ≤ D−1. $0 users stay in N."""
    if users_slice.empty:
        return pd.DataFrame()

    build = ns["build_user_revenue_cums"]
    sum_cum = ns["sum_cum_at_idx"]

    u_in = users_slice.copy()
    u_in["population"] = population
    u_base, daily = build(u_in, revenue_df, max_day=max_day)
    if u_base.empty:
        return pd.DataFrame()

    n_users = int(u_base["__uid__"].nunique())
    n_dates = int(u_base["cost_date"].nunique())
    rows = []
    for day in range(1, max_day + 1):
        sums = sum_cum(daily, cohort_users=u_base, idx=day - 1, caps=None)
        total = float(sums["sum_cum"].sum()) if len(sums) else 0.0
        arpu = total / n_users if n_users else np.nan
        rows.append(
            dict(
                population=population,
                day=day,
                n_users=n_users,
                n_cost_dates=n_dates,
                sum_cum=total,
                actual_arpu=arpu,
            )
        )
    out = pd.DataFrame(rows)
    arpu_120 = float(out.loc[out["day"] == max_day, "actual_arpu"].iloc[0])
    if not np.isfinite(arpu_120) or arpu_120 == 0:
        out["actual_ratio"] = np.nan
    else:
        out["actual_ratio"] = out["actual_arpu"] / arpu_120
    out["actual_arpu_120"] = arpu_120
    return out


def build_actuals(ns, brand: str, eval_users, eval_rev, curve_pops) -> pd.DataFrame:
    eval_users = eval_users.copy()
    eval_users["cost_date"] = _norm_cost(eval_users["cost_date"])
    all_dates = sorted(eval_users["cost_date"].unique())
    slices = {
        "overall": None,
        "2026-04-10": [pd.Timestamp("2026-04-10").date()],
        "2026-04-14": [pd.Timestamp("2026-04-14").date()],
    }
    for d in all_dates:
        key = str(d)
        if key not in slices:
            slices[key] = [d]

    frames = []
    pops = list(curve_pops) + ["Blended"]
    for pop in pops:
        if pop == "Blended":
            u_pop = eval_users
        else:
            u_pop = eval_users.loc[eval_users["population"] == pop]
        for slice_name, dates in slices.items():
            u_slice = u_pop if dates is None else u_pop.loc[u_pop["cost_date"].isin(dates)]
            if u_slice.empty:
                continue
            path = realized_arpu_path(ns, u_slice, eval_rev, population=pop)
            if path.empty:
                continue
            path.insert(0, "brand", brand)
            path.insert(2, "slice", slice_name)
            frames.append(path)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def ape(err, denom):
    denom = np.asarray(denom, dtype=float)
    err = np.asarray(err, dtype=float)
    out = np.full(err.shape, np.nan)
    ok = np.isfinite(denom) & (np.abs(denom) > APE_NEAR_ZERO) & np.isfinite(err)
    out[ok] = err[ok] / np.abs(denom[ok])
    return out


def compare_paths(frozen_goals: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    g = frozen_goals.loc[frozen_goals["goal_horizon"] == GOAL_HORIZON].copy()
    keep = [
        "brand",
        "population",
        "day",
        "raw_goal_ratio",
        "organic_share",
        "adjusted_goal_ratio",
        "ARPU_nominal",
        "ARPU_at_horizon",
    ]
    keep = [c for c in keep if c in g.columns]
    g = g[keep]
    m = actuals.merge(g, on=["brand", "population", "day"], how="left")

    m["shape_signed_bias"] = m["actual_ratio"] - m["raw_goal_ratio"]
    m["shape_ae"] = m["shape_signed_bias"].abs()
    m["shape_ape"] = ape(m["shape_ae"], m["raw_goal_ratio"])

    m["adj_signed_bias"] = m["actual_ratio"] - m["adjusted_goal_ratio"]
    m["adj_ae"] = m["adj_signed_bias"].abs()
    m["adj_ape"] = ape(m["adj_ae"], m["adjusted_goal_ratio"])

    m["level_signed_bias"] = m["actual_arpu"] - m["ARPU_nominal"]
    m["level_ae"] = m["level_signed_bias"].abs()
    m["level_ape"] = ape(m["level_ae"], m["ARPU_nominal"])
    return m


def milestone_table(compare_df: pd.DataFrame) -> pd.DataFrame:
    return (
        compare_df.loc[compare_df["day"].isin(MILESTONE_DAYS)]
        .sort_values(["brand", "population", "slice", "day"])
        .reset_index(drop=True)
    )


def error_summary(compare_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (brand, pop, sl), sub in compare_df.groupby(
        ["brand", "population", "slice"], observed=True
    ):
        sub = sub.loc[sub["day"].notna()].copy()
        if sub.empty:
            continue

        def pack(prefix, ae_col, bias_col, ape_col):
            ae = sub[ae_col].dropna()
            bias = sub[bias_col].dropna()
            ap = sub[ape_col].dropna()
            return {
                f"{prefix}_n_days": int(ae.shape[0]),
                f"{prefix}_mae": float(ae.mean()) if len(ae) else np.nan,
                f"{prefix}_median_ae": float(ae.median()) if len(ae) else np.nan,
                f"{prefix}_bias": float(bias.mean()) if len(bias) else np.nan,
                f"{prefix}_median_ape": float(ap.median()) if len(ap) else np.nan,
            }

        rec = dict(brand=brand, population=pop, slice=sl, n_users=int(sub["n_users"].iloc[0]))
        rec.update(pack("shape", "shape_ae", "shape_signed_bias", "shape_ape"))
        rec.update(pack("level", "level_ae", "level_signed_bias", "level_ape"))
        rec.update(pack("adj", "adj_ae", "adj_signed_bias", "adj_ape"))
        rows.append(rec)
    return pd.DataFrame(rows).sort_values(["brand", "population", "slice"]).reset_index(drop=True)


def plot_paths(compare_df: pd.DataFrame, out_dir: Path) -> list[str]:
    written = []
    overall = compare_df.loc[compare_df["slice"] == "overall"]
    for (brand, pop), sub in overall.groupby(["brand", "population"], observed=True):
        sub = sub.sort_values("day")
        if sub.empty:
            continue
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 7.2), sharex=True)

        axes[0].plot(sub["day"], sub["raw_goal_ratio"], label="Frozen raw (primary)", color="#1f4e79", lw=2)
        axes[0].plot(sub["day"], sub["actual_ratio"], label="Actual ARPU(d)/ARPU(120)", color="#c45911", lw=2)
        if sub["adjusted_goal_ratio"].notna().any():
            axes[0].plot(
                sub["day"],
                sub["adjusted_goal_ratio"],
                label="Frozen adjusted (haircut)",
                color="#7f7f7f",
                lw=1.2,
                ls="--",
            )
        axes[0].set_ylabel("Ratio to day 120")
        axes[0].set_title(f"{brand} · {pop} — shape (primary)")
        axes[0].legend(loc="lower right", fontsize=8)
        axes[0].grid(True, alpha=0.25)

        axes[1].plot(sub["day"], sub["ARPU_nominal"], label="Frozen ARPU_nominal", color="#1f4e79", lw=2)
        axes[1].plot(sub["day"], sub["actual_arpu"], label="Actual ARPU (no winsor)", color="#c45911", lw=2)
        axes[1].set_xlabel("Life day D  (dsi ≤ D−1)")
        axes[1].set_ylabel("ARPU ($)")
        axes[1].set_title(f"{brand} · {pop} — level (secondary)")
        axes[1].legend(loc="lower right", fontsize=8)
        axes[1].grid(True, alpha=0.25)

        fig.tight_layout()
        fname = f"plot_{brand}_{pop.replace(' ', '_')}.png"
        path = out_dir / fname
        fig.savefig(path, dpi=140)
        plt.close(fig)
        written.append(fname)
    return written


def _fmt_pct(x):
    if x is None or not np.isfinite(x):
        return "—"
    return f"{100.0 * x:.1f}%"


def _fmt_num(x, digits=3):
    if x is None or not np.isfinite(x):
        return "—"
    return f"{x:.{digits}f}"


def write_writeup(out_dir: Path, milestones: pd.DataFrame, summary: pd.DataFrame) -> None:
    lines = [
        "*Lee Jerusalmy*",
        "",
        "# Did horizon-120 daily goals match Apr 10–14 reality?",
        "",
        "Freeze **2026-04-10**. Combined as-is (winsor / CV / lookback 35 / organic). "
        "Patches through 120 only. Actuals **not** winsorized.",
        "",
        "**Primary:** shape — actual `ARPU(d) / ARPU(120)` vs frozen `raw_goal_ratio`.",
        "",
        "`ARPU_nominal` is the stitched model curve **before** organic. "
        "Organic hits the ratio only (`adjusted_goal_ratio`).",
        "",
        "## Overall (5 dates pooled) — shape error",
        "",
        "| Brand | Population | Users | Shape MAE | Median AE | Bias (actual − raw) | Day-120 actual ARPU | Frozen ARPU_120 |",
        "|-------|------------|------:|----------:|----------:|--------------------:|--------------------:|----------------:|",
    ]
    ov = summary.loc[summary["slice"] == "overall"]
    for _, r in ov.iterrows():
        d120 = milestones.loc[
            (milestones["brand"] == r["brand"])
            & (milestones["population"] == r["population"])
            & (milestones["slice"] == "overall")
            & (milestones["day"] == 120)
        ]
        act = float(d120["actual_arpu"].iloc[0]) if len(d120) else np.nan
        frz = float(d120["ARPU_nominal"].iloc[0]) if len(d120) else np.nan
        lines.append(
            f"| {r['brand']} | {r['population']} | {int(r['n_users']):,} | "
            f"{_fmt_num(r['shape_mae'])} | {_fmt_num(r['shape_median_ae'])} | "
            f"{_fmt_num(r['shape_bias'])} | {_fmt_num(act, 2)} | {_fmt_num(frz, 2)} |"
        )

    lines += [
        "",
        "Bias > 0 means actual pace ran **ahead** of the frozen raw path.",
        "",
        "## Milestones — overall shape (raw vs actual ratio)",
        "",
        "| Brand | Pop | Day | Frozen raw | Actual ratio | AE | APE | Frozen $ | Actual $ |",
        "|-------|-----|----:|-----------:|-------------:|---:|----:|---------:|---------:|",
    ]
    ms = milestones.loc[milestones["slice"] == "overall"]
    for _, r in ms.iterrows():
        lines.append(
            f"| {r['brand']} | {r['population']} | {int(r['day'])} | "
            f"{_fmt_num(r['raw_goal_ratio'])} | {_fmt_num(r['actual_ratio'])} | "
            f"{_fmt_num(r['shape_ae'])} | {_fmt_pct(r['shape_ape'])} | "
            f"{_fmt_num(r['ARPU_nominal'], 2)} | {_fmt_num(r['actual_arpu'], 2)} |"
        )

    lines += [
        "",
        "## 10 Apr vs 14 Apr — shape MAE vs the same frozen path",
        "",
        "| Brand | Population | 10 Apr MAE | 14 Apr MAE | 10 Apr bias | 14 Apr bias |",
        "|-------|------------|-----------:|-----------:|------------:|------------:|",
    ]
    for (brand, pop), sub in summary.groupby(["brand", "population"], observed=True):
        a = sub.loc[sub["slice"] == "2026-04-10"]
        b = sub.loc[sub["slice"] == "2026-04-14"]
        if a.empty or b.empty:
            continue
        lines.append(
            f"| {brand} | {pop} | {_fmt_num(a['shape_mae'].iloc[0])} | "
            f"{_fmt_num(b['shape_mae'].iloc[0])} | "
            f"{_fmt_num(a['shape_bias'].iloc[0])} | {_fmt_num(b['shape_bias'].iloc[0])} |"
        )

    lines += [
        "",
        "## How to read this",
        "",
        "- **Shape (primary):** did the realized *pace* to day 120 match the frozen raw path?",
        "- **Level:** same shape can still miss dollars (`actual ARPU` vs `ARPU_nominal`).",
        "- **Adjusted:** sits below the actual ratio by ~organic, by design. Not the verdict.",
        "- Actuals include $0 users in N. No fill of missing days.",
        "",
        "Not a methodology lock.",
        "",
    ]
    (out_dir / "WRITEUP.md").write_text("\n".join(lines))


def write_export(
    out_dir: Path,
    *,
    frozen_goals,
    actuals,
    compare_df,
    milestones,
    summary,
    count_df,
    plot_names,
    run_ts: str,
    extra_meta: dict | None = None,
    label_md: str | None = None,
    write_writeup_fn=None,
) -> None:
    frozen_goals.to_csv(out_dir / "frozen_goals_h120.csv", index=False)
    actuals.to_csv(out_dir / "actuals_daily.csv", index=False)
    compare_df.to_csv(out_dir / "compare_daily.csv", index=False)
    milestones.to_csv(out_dir / "compare_milestones.csv", index=False)
    summary.to_csv(out_dir / "error_summary.csv", index=False)
    if count_df is not None and len(count_df):
        count_df.to_csv(out_dir / "eval_user_counts.csv", index=False)
    meta = {
        "as_of_date": str(FREEZE_AS_OF.date()),
        "eval_cost_start": str(EVAL_START.date()),
        "eval_cost_end": str(EVAL_END.date()),
        "goal_horizon": GOAL_HORIZON,
        "lookback_cohorts": LOOKBACK_COHORTS,
        "patches": str(list(NARROW_PATCHES)),
        "sql_floor": str(SQL_FLOOR.date()),
        "eval_deposit_end": str(EVAL_DEPOSIT_END.date()),
        "actuals_winsorized": False,
        "primary": "shape_raw_vs_actual_ratio",
        "arpu_nominal_after_organic": False,
        "run_ts": run_ts,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "plots": ";".join(plot_names),
    }
    if extra_meta:
        meta.update(extra_meta)
    pd.DataFrame([meta]).to_csv(out_dir / "run_meta.csv", index=False)
    (out_dir / "LABEL.md").write_text(
        label_md
        or (
            "*Lee Jerusalmy*\n\n"
            "# 2026-04-10 RP+LS goal-120 realized check\n\n"
            "Frozen Combined daily goals (horizon 120) as of **2026-04-10**, "
            "scored against realized Apr 10–14 paths. "
            "Primary = shape (raw vs actual ARPU(d)/ARPU(120)). "
            "Actuals not winsorized. Patches through 120 only. "
            "Not a methodology lock.\n"
        )
    )
    (write_writeup_fn or write_writeup)(out_dir, milestones, summary)


def setup_local_creds() -> None:
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return
    if CREDS.is_file():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDS)
        log(f"creds {CREDS.name}")
        return
    raise FileNotFoundError(
        "No BQ credentials. Set GOOGLE_APPLICATION_CREDENTIALS or place "
        "the project JSON under lee_project/."
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="H=120 freeze 2026-04-10 vs Apr 10–14 actuals")
    parser.add_argument("--count-only", action="store_true", help="Cheap eval-user counts, then stop")
    parser.add_argument("--no-cache", action="store_true", help="Ignore parquet cache")
    args = parser.parse_args(argv)

    log("=== goal120 realized check ===")
    log(f"freeze={FREEZE_AS_OF.date()}  eval={EVAL_START.date()}..{EVAL_END.date()}")
    log(f"sql_floor={SQL_FLOOR.date()}  eval_deposit_end={EVAL_DEPOSIT_END.date()}")
    log("primary=shape  actuals not winsorized  ARPU_nominal is before organic")

    try:
        import google.colab  # noqa: F401

        in_colab = True
    except ImportError:
        in_colab = False
    if not in_colab:
        setup_local_creds()

    ns: dict = {"__name__": "combined_helpers"}
    exec_combined_helpers(ns)
    apply_check_calendar(ns)

    count_df = count_eval_users(ns)
    print("\nEval user counts (cost_date 2026-04-10..14):\n")
    print(count_df.to_string(index=False))
    print()
    if args.count_only:
        log("count-only — stop")
        return 0

    frozen_parts = []
    actual_parts = []
    for brand_key in ns["RUN_BRANDS"]:
        cfg = ns["BRAND_CONFIGS"][brand_key]
        brand = cfg["brand"]
        users_df, revenue_df = load_narrow_tables(ns, cfg, use_cache=not args.no_cache)
        train_u, train_r, eval_u, eval_r = split_train_eval(users_df, revenue_df)
        log(
            f"[{brand}] train users={len(train_u):,}  eval users={len(eval_u):,}  "
            f"train rev rows={len(train_r):,}"
        )
        result = run_frozen_goals(ns, brand_key, train_u, train_r)
        goals = result["goals"]
        if goals is None or goals.empty:
            log(f"[{brand}] WARNING: no frozen goals")
        else:
            frozen_parts.append(goals)
        actuals = build_actuals(ns, brand, eval_u, eval_r, cfg["populations"])
        log(f"[{brand}] actual rows={len(actuals):,}")
        actual_parts.append(actuals)

    frozen_goals = pd.concat(frozen_parts, ignore_index=True) if frozen_parts else pd.DataFrame()
    actuals = pd.concat(actual_parts, ignore_index=True) if actual_parts else pd.DataFrame()
    if frozen_goals.empty or actuals.empty:
        log("ERROR: missing frozen goals or actuals — no export")
        return 1

    compare_df = compare_paths(frozen_goals, actuals)
    milestones = milestone_table(compare_df)
    summary = error_summary(compare_df)

    run_ts = datetime.now().strftime("%H%M%S")
    out_dir = RUNS / f"2026-04-10_rp_ls_goal120_realized_{run_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_names = plot_paths(compare_df, out_dir)
    write_export(
        out_dir,
        frozen_goals=frozen_goals,
        actuals=actuals,
        compare_df=compare_df,
        milestones=milestones,
        summary=summary,
        count_df=count_df,
        plot_names=plot_names,
        run_ts=run_ts,
    )
    log(f"exported {out_dir}")
    print("\nOverall shape summary:\n")
    cols = [
        "brand",
        "population",
        "n_users",
        "shape_mae",
        "shape_median_ae",
        "shape_bias",
        "level_mae",
        "level_bias",
    ]
    print(summary.loc[summary["slice"] == "overall", cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    rc = main()
    try:
        get_ipython()  # Colab / IPython — do not SystemExit
    except NameError:
        sys.exit(rc)
