#!/usr/bin/env python3
"""Compare provisional lonestar/App goal methods while post-launch history is short.

Methods:
  - native_ls_app        — full Combined pipeline on LS App only (may explode in the tail)
  - ls_web_donor         — LS Web curve shape + LS App own D1 level
  - rp_app_donor         — RP App curve shape + LS App own D1 level
  - hybrid_donor         — average LS Web + RP App shape, LS App own D1 level
  - native_early_rp_tail — LS App native through last measured day, then RP App day-growth to 120

Primary score: short-horizon shape on fixed LS App eval users (equal N through D*).
Does not change generic Combined or DECISIONS.md.
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
APRIL = MG_ROOT / "experiments" / "goal120_realized_2026-04-10"
sys.path.insert(0, str(APRIL))
import run_goal120_realized as base  # noqa: E402

SCRATCH_NB = HERE / "Marketing_Goals_Combined_RP_LS_Colab.ipynb"
CACHE = MG_ROOT / "experiments" / "cache" / "ls_app_bootstrap"
RUNS = MG_ROOT / "runs"
CREDS = PROJECT_ROOT / "oceanic-citadel-454608-d2-e116e15558ce.json"

LAUNCH = pd.Timestamp("2026-07-16").normalize()
OBS_END = pd.Timestamp("2026-08-17").normalize()
FREEZE = OBS_END
EVAL_START = LAUNCH
EVAL_END = OBS_END
SLICE_LAUNCH_DAY = "launch_day"
SLICE_LAUNCH_WEEK = "launch_week"
LAUNCH_WEEK_END = pd.Timestamp("2026-07-22").normalize()
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
CHECKPOINTS = (1, 3, 7, 14, 21, 28)
HORIZON_DAYS = (1, 7, 14, 30, 60, 90, 120)
METHODS = (
    "native_ls_app",
    "ls_web_donor",
    "rp_app_donor",
    "hybrid_donor",
    "native_early_rp_tail",
)
TARGET_BRAND = "lonestar"
TARGET_POP = "App"


def log(msg: str) -> None:
    print(f"{datetime.now().strftime('%H:%M:%S')}  {msg}", flush=True)


def days_lived(cost_date, obs_end) -> int:
    return (pd.Timestamp(obs_end).date() - pd.Timestamp(cost_date).date()).days + 1


def ls_users_sql(cfg: dict, cost_start, cost_end) -> str:
    """Lonestar population map with App + RP-style scope/bucket."""
    cost_table = cfg["cost_table"]
    excl_sql = ", ".join(str(a) for a in cfg["exclude_affids"])
    start = pd.Timestamp(cost_start).date()
    end = pd.Timestamp(cost_end).date()
    return f"""
    SELECT
      id,
      CASE
        WHEN affid IN (63, 4432, 4551, 4698, 5048, 5125, 7120, 7253, 7260, 8331, 8345) THEN 'Web'
        WHEN affid = 1 THEN 'App'
        WHEN affid IN (64, 71)  THEN 'PPC'
        WHEN affid IN (0, 78)   THEN 'Organic'
        ELSE 'Affiliate'
      END AS population,
      CASE WHEN affid = 1 THEN 'app' ELSE 'non_app' END AS scope,
      CASE
        WHEN affid = 1 AND channel_type = 'app_organic' THEN 'organic'
        WHEN affid = 1                                   THEN 'acquired'
        WHEN affid IN (0, 78)                            THEN 'organic'
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


def install_calendar() -> None:
    base.FREEZE_AS_OF = FREEZE
    base.EVAL_START = EVAL_START
    base.EVAL_END = EVAL_END
    base.EVAL_DEPOSIT_END = OBS_END + pd.Timedelta(days=GOAL_HORIZON - 1)
    base.SQL_FLOOR = (
        FREEZE - pd.Timedelta(days=GOAL_HORIZON + LOOKBACK_COHORTS + 5)
    ).normalize()
    base.GOAL_HORIZON = GOAL_HORIZON
    base.CACHE = CACHE
    base.MILESTONE_DAYS = CHECKPOINTS
    log(
        f"calendar: launch={LAUNCH.date()}  freeze={FREEZE.date()}  "
        f"eval={EVAL_START.date()}..{EVAL_END.date()}  obs_end={OBS_END.date()}  "
        f"max life days (launch day)={days_lived(LAUNCH, OBS_END)}"
    )


def load_helpers() -> dict:
    ns: dict = {"__name__": "ls_app_bootstrap_helpers"}
    base.exec_combined_helpers(ns, nb_path=SCRATCH_NB)
    ns["AS_OF_DATE"] = FREEZE
    ns["PATCHES"] = NARROW_PATCHES
    ns["GOAL_HORIZONS"] = [GOAL_HORIZON]
    ns["CHECKPOINTS"] = [GOAL_HORIZON]
    ns["LOOKBACK_COHORTS"] = LOOKBACK_COHORTS
    ns["MONITOR_STEPS"] = False
    ns["RUN_BRANDS"] = ["realprize", "lonestar"]
    return ns


def read_gbq(ns: dict, sql: str):
    return ns["read_gbq"](sql, project_id=ns["project_id"], use_bqstorage_api=True)


def normalize_users(users_df: pd.DataFrame) -> pd.DataFrame:
    u = users_df.copy()
    u["cost_date"] = base._norm_cost(u["cost_date"])
    return u


def load_brand_tables(ns: dict, brand_key: str, *, use_cache: bool):
    cfg = ns["BRAND_CONFIGS"][brand_key]
    brand = cfg["brand"]
    CACHE.mkdir(parents=True, exist_ok=True)
    u_path = CACHE / f"{brand}_users.parquet"
    r_path = CACHE / f"{brand}_revenue.parquet"
    if use_cache and u_path.exists() and r_path.exists():
        log(f"[{brand}] cache hit {CACHE.name}")
        return normalize_users(pd.read_parquet(u_path)), pd.read_parquet(r_path)

    users_sql = ls_users_sql if brand == "lonestar" else base.users_sql
    log(
        f"[{brand}] BQ pull  users {base.SQL_FLOOR.date()}→{EVAL_END.date()}  "
        f"deposits {base.SQL_FLOOR.date()}→{base.EVAL_DEPOSIT_END.date()}"
    )
    users_df = read_gbq(ns, users_sql(cfg, base.SQL_FLOOR, EVAL_END))
    revenue_df = read_gbq(
        ns, base.revenue_sql(cfg, base.SQL_FLOOR, base.EVAL_DEPOSIT_END)
    )
    users_df = normalize_users(users_df)
    revenue_df["date"] = pd.to_datetime(revenue_df["date"]).dt.date
    users_df.to_parquet(u_path, index=False)
    revenue_df.to_parquet(r_path, index=False)
    log(f"[{brand}] cached users={len(users_df):,}  rev={len(revenue_df):,}")
    return users_df, revenue_df


def split_train_eval(users_df, revenue_df):
    freeze = FREEZE.date()
    eval_dates = set(
        pd.date_range(EVAL_START, EVAL_END, freq="D").date
    )
    u = users_df.copy()
    r = revenue_df.copy()
    u["cost_date"] = base._norm_cost(u["cost_date"])
    train_users = u.loc[u["cost_date"] < freeze].copy()
    train_rev = r.loc[r["date"] < freeze].copy()
    eval_users = u.loc[
        (u["cost_date"] >= LAUNCH.date()) & (u["cost_date"].isin(eval_dates))
    ].copy()
    eval_rev = r.copy()
    return train_users, train_rev, eval_users, eval_rev


def curve_for_pop(curve_df: pd.DataFrame, population: str) -> pd.DataFrame:
    out = curve_df.loc[curve_df["population"] == population].copy()
    if out.empty:
        return out
    return out.drop_duplicates(subset="day").sort_values("day").reset_index(drop=True)


def app_d1_anchor(native_curve: pd.DataFrame, ns: dict, train_users, train_rev) -> float:
    """Day-1 ARPU anchor for LS App from native curve or direct compute."""
    native = curve_for_pop(native_curve, TARGET_POP)
    if not native.empty and "ARPU_nominal" in native.columns:
        d1 = native.loc[native["day"] == 1, "ARPU_nominal"]
        if len(d1) and np.isfinite(float(d1.iloc[0])) and float(d1.iloc[0]) > 0:
            return float(d1.iloc[0])

    u_app = train_users.loc[train_users["population"] == TARGET_POP].copy()
    if u_app.empty:
        raise RuntimeError("No LS App training users — cannot anchor D1.")
    path = base.realized_arpu_path(
        ns, u_app, train_rev, population=TARGET_POP, max_day=1
    )
    if path.empty:
        raise RuntimeError("Could not compute LS App D1 from training users.")
    d1 = float(path.loc[path["day"] == 1, "actual_arpu"].iloc[0])
    if not np.isfinite(d1) or d1 <= 0:
        raise RuntimeError(f"Invalid LS App D1 anchor: {d1}")
    return d1


def scale_donor_curve(
    donor_curve: pd.DataFrame,
    *,
    donor_pop: str,
    target_d1: float,
    target_pop: str = TARGET_POP,
) -> pd.DataFrame:
    donor = curve_for_pop(donor_curve, donor_pop)
    if donor.empty:
        raise RuntimeError(f"Donor curve empty for population={donor_pop!r}")
    d1_row = donor.loc[donor["day"] == 1]
    if d1_row.empty:
        raise RuntimeError(f"Donor {donor_pop} missing day 1.")
    donor_d1 = float(d1_row["ARPU_nominal"].iloc[0])
    if not np.isfinite(donor_d1) or donor_d1 <= 0:
        raise RuntimeError(f"Invalid donor D1 for {donor_pop}: {donor_d1}")

    out = donor.copy()
    out["population"] = target_pop
    out["ARPU_nominal"] = target_d1 * (out["ARPU_nominal"] / donor_d1)
    if "is_extrapolated" not in out.columns:
        out["is_extrapolated"] = False
    return out


def hybrid_donor_curve(
    web_curve: pd.DataFrame,
    rp_app_curve: pd.DataFrame,
    *,
    target_d1: float,
    target_pop: str = TARGET_POP,
) -> pd.DataFrame:
    web = curve_for_pop(web_curve, "Web")
    rp = curve_for_pop(rp_app_curve, "App")
    if web.empty or rp.empty:
        raise RuntimeError("Hybrid donor requires LS Web and RP App curves.")

    web = web.set_index("day")
    rp = rp.set_index("day")
    days = sorted(set(web.index) & set(rp.index))
    if 1 not in days:
        raise RuntimeError("Hybrid donor missing day 1 overlap.")

    web_d1 = float(web.loc[1, "ARPU_nominal"])
    rp_d1 = float(rp.loc[1, "ARPU_nominal"])
    rows = []
    for day in days:
        web_shape = float(web.loc[day, "ARPU_nominal"]) / web_d1
        rp_shape = float(rp.loc[day, "ARPU_nominal"]) / rp_d1
        hybrid_shape = 0.5 * (web_shape + rp_shape)
        row = web.loc[day].to_dict() if day in web.index else rp.loc[day].to_dict()
        row["day"] = day
        row["population"] = target_pop
        row["ARPU_nominal"] = target_d1 * hybrid_shape
        row["is_extrapolated"] = bool(row.get("is_extrapolated", False))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("day").reset_index(drop=True)


def last_measured_day(native: pd.DataFrame) -> int:
    """Last life day that came from measured patches, not LS tail extrapolation."""
    if native.empty:
        raise RuntimeError("Native LS App curve is empty.")
    if "is_extrapolated" in native.columns:
        flag = native["is_extrapolated"].fillna(False).astype(bool)
        real = native.loc[~flag]
        if not real.empty:
            return int(real["day"].max())
    return int(native["day"].max())


def native_early_rp_tail_curve(
    native_curve: pd.DataFrame,
    rp_app_curve: pd.DataFrame,
    *,
    target_pop: str = TARGET_POP,
    max_day: int | None = None,
) -> tuple[pd.DataFrame, int]:
    """Keep native LS App through last measured day; dress RP App growth after that.

    After splice day S:
      ARPU(d) = ARPU(d-1) × (ARPU_RP(d) / ARPU_RP(d-1))
    """
    native = curve_for_pop(native_curve, target_pop)
    rp = curve_for_pop(rp_app_curve, "App")
    if native.empty:
        raise RuntimeError("native_early_rp_tail needs a native LS App curve.")
    if rp.empty:
        raise RuntimeError("native_early_rp_tail needs an RP App curve.")

    horizon = int(max_day) if max_day is not None else GOAL_HORIZON
    splice = last_measured_day(native)
    native = native.sort_values("day")
    rp = rp.drop_duplicates(subset="day").set_index("day")

    keep = native.loc[native["day"] <= splice].copy()
    keep["population"] = target_pop
    keep["is_extrapolated"] = False

    last_arpu = float(keep.loc[keep["day"] == splice, "ARPU_nominal"].iloc[0])
    extra_rows = []
    for day in range(splice + 1, horizon + 1):
        if day not in rp.index or (day - 1) not in rp.index:
            continue
        rp_prev = float(rp.loc[day - 1, "ARPU_nominal"])
        rp_now = float(rp.loc[day, "ARPU_nominal"])
        growth = 1.0 if (not np.isfinite(rp_prev) or rp_prev <= 0) else rp_now / rp_prev
        last_arpu = last_arpu * growth
        row = rp.loc[day].to_dict()
        row["day"] = day
        row["population"] = target_pop
        row["ARPU_nominal"] = last_arpu
        row["is_extrapolated"] = True
        extra_rows.append(row)

    out = pd.concat([keep, pd.DataFrame(extra_rows)], ignore_index=True)
    out = out.sort_values("day").drop_duplicates(subset="day").reset_index(drop=True)
    end_day = int(out["day"].max())
    log(
        f"native_early_rp_tail: splice after day {splice}  "
        f"ARPU({splice})=${last_measured_arpu(keep, splice):.4f}  "
        f"ARPU({end_day})=${float(out.loc[out['day'] == end_day, 'ARPU_nominal'].iloc[0]):.2f}"
    )
    return out, splice


def last_measured_arpu(curve: pd.DataFrame, day: int) -> float:
    return float(curve.loc[curve["day"] == day, "ARPU_nominal"].iloc[0])


def goals_from_curve(
    ns: dict,
    curve_df: pd.DataFrame,
    organic_df: pd.DataFrame,
    *,
    method: str,
) -> pd.DataFrame:
    goals = ns["build_goals"](
        curve_df,
        organic_df,
        [TARGET_POP],
        goal_horizons=[GOAL_HORIZON],
        organic_share_cap_horizon=ns.get("ORGANIC_SHARE_CAP_HORIZON"),
    )
    if goals.empty:
        return goals
    goals.insert(0, "brand", TARGET_BRAND)
    goals.insert(1, "method", method)
    return goals


def d_star_for_users(users: pd.DataFrame) -> int:
    if users.empty:
        return 0
    lived = users["cost_date"].map(lambda c: days_lived(c, OBS_END))
    return int(lived.min())


def eval_slices(eval_app: pd.DataFrame) -> dict[str, pd.DataFrame]:
    launch_day = LAUNCH.date()
    launch_week = set(
        pd.date_range(LAUNCH, LAUNCH_WEEK_END, freq="D").date
    )
    return {
        SLICE_LAUNCH_DAY: eval_app.loc[eval_app["cost_date"] == launch_day].copy(),
        SLICE_LAUNCH_WEEK: eval_app.loc[eval_app["cost_date"].isin(launch_week)].copy(),
    }


def build_actuals(ns, eval_users_app, eval_rev) -> pd.DataFrame:
    frames = []
    for slice_name, users_slice in eval_slices(eval_users_app).items():
        if users_slice.empty:
            continue
        d_star = d_star_for_users(users_slice)
        if d_star < 1:
            continue
        path = base.realized_arpu_path(
            ns, users_slice, eval_rev, population=TARGET_POP, max_day=d_star
        )
        if path.empty:
            continue
        path = path.rename(columns={"actual_arpu_120": "actual_arpu_dstar"})
        path["d_star"] = d_star
        path["shape_ok"] = True
        path.insert(0, "brand", TARGET_BRAND)
        path.insert(2, "slice", slice_name)
        frames.append(path)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def compare_method(goals: pd.DataFrame, actuals_slice: pd.DataFrame) -> pd.DataFrame:
    g = goals.loc[goals["goal_horizon"] == GOAL_HORIZON].copy()
    keep = [
        "brand",
        "method",
        "population",
        "day",
        "raw_goal_ratio",
        "organic_share",
        "adjusted_goal_ratio",
        "ARPU_nominal",
        "ARPU_at_horizon",
    ]
    keep = [c for c in keep if c in g.columns]
    m = actuals_slice.merge(g[keep], on=["brand", "population", "day"], how="left")
    d_star = int(actuals_slice["d_star"].iloc[0])
    slice_name = actuals_slice["slice"].iloc[0]
    act_end = float(actuals_slice.loc[actuals_slice["day"] == d_star, "actual_arpu"].iloc[0])
    frz_end = float(m.loc[m["day"] == d_star, "ARPU_nominal"].iloc[0])
    if np.isfinite(act_end) and act_end != 0:
        m["actual_ratio"] = m["actual_arpu"] / act_end
    else:
        m["actual_ratio"] = np.nan
    if np.isfinite(frz_end) and frz_end != 0:
        m["frozen_shape"] = m["ARPU_nominal"] / frz_end
    else:
        m["frozen_shape"] = np.nan
    m["shape_signed_bias"] = m["actual_ratio"] - m["frozen_shape"]
    m["shape_ae"] = m["shape_signed_bias"].abs()
    m["shape_ape"] = base.ape(m["shape_ae"], m["frozen_shape"])
    m["level_signed_bias"] = m["actual_arpu"] - m["ARPU_nominal"]
    m["level_ae"] = m["level_signed_bias"].abs()
    m["level_ape"] = base.ape(m["level_ae"], m["ARPU_nominal"])
    m["d_star"] = d_star
    m["slice"] = slice_name
    m["shape_ok"] = True
    return m


def method_summary(compare_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (method, sl), sub in compare_df.groupby(["method", "slice"], observed=True):
        sub = sub.sort_values("day")
        ae = sub["shape_ae"].dropna()
        bias = sub["shape_signed_bias"].dropna()
        rows.append(
            dict(
                brand=TARGET_BRAND,
                population=TARGET_POP,
                slice=sl,
                method=method,
                n_users=int(sub["n_users"].iloc[0]),
                d_star=int(sub["d_star"].iloc[0]),
                shape_n_days=int(ae.shape[0]),
                shape_mae=float(ae.mean()) if len(ae) else np.nan,
                shape_median_ae=float(ae.median()) if len(ae) else np.nan,
                shape_bias=float(bias.mean()) if len(bias) else np.nan,
                level_mae=float(sub["level_ae"].mean()),
            )
        )
    out = pd.DataFrame(rows)
    out = out.sort_values(["slice", "shape_mae"]).reset_index(drop=True)
    out["rank"] = out.groupby("slice", observed=True).cumcount() + 1
    return out


def compare_methods(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sl, part in summary.groupby("slice", observed=True):
        best = part.loc[part["rank"] == 1, "method"].iloc[0]
        for _, r in part.iterrows():
            rows.append(
                dict(
                    slice=sl,
                    method=r["method"],
                    shape_mae=r["shape_mae"],
                    shape_bias=r["shape_bias"],
                    d_star=r["d_star"],
                    n_users=r["n_users"],
                    rank=int(r["rank"]),
                    winner=(r["method"] == best),
                )
            )
    return pd.DataFrame(rows)


def plot_methods(compare_all: pd.DataFrame, out_dir: Path) -> list[str]:
    written = []
    for slice_name, slice_df in compare_all.groupby("slice", observed=True):
        d_star = int(slice_df["d_star"].iloc[0])
        fig, axes = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True)
        colors = {
            "native_ls_app": "#1f4e79",
            "ls_web_donor": "#2ca02c",
            "rp_app_donor": "#ff7f0e",
            "hybrid_donor": "#9467bd",
            "native_early_rp_tail": "#17becf",
        }
        for method, sub in slice_df.groupby("method", observed=True):
            sub = sub.sort_values("day")
            axes[0].plot(
                sub["day"],
                sub["frozen_shape"],
                label=method,
                color=colors.get(method, None),
                lw=1.8,
            )
        actual = slice_df.drop_duplicates("day").sort_values("day")
        axes[0].plot(
            actual["day"],
            actual["actual_ratio"],
            label="Actual",
            color="#c45911",
            lw=2.4,
        )
        axes[0].set_ylabel("Ratio to D*")
        axes[0].set_title(f"lonestar · App · {slice_name} — shape so far (D*={d_star})")
        axes[0].legend(loc="lower right", fontsize=8)
        axes[0].grid(True, alpha=0.25)

        for method, sub in slice_df.groupby("method", observed=True):
            sub = sub.sort_values("day")
            axes[1].plot(
                sub["day"],
                sub["ARPU_nominal"],
                label=method,
                color=colors.get(method, None),
                lw=1.8,
            )
        axes[1].plot(
            actual["day"],
            actual["actual_arpu"],
            label="Actual",
            color="#c45911",
            lw=2.4,
        )
        axes[1].set_xlabel("Life day D  (dsi ≤ D−1)")
        axes[1].set_ylabel("ARPU ($)")
        axes[1].set_title("Level (secondary)")
        axes[1].legend(loc="lower right", fontsize=8)
        axes[1].grid(True, alpha=0.25)
        fig.tight_layout()
        fname = f"plot_ls_app_{slice_name}.png"
        fig.savefig(out_dir / fname, dpi=140)
        plt.close(fig)
        written.append(fname)
    return written


def plot_horizon_levels(goals_all: pd.DataFrame, out_dir: Path) -> list[str]:
    """Full H=120 ARPU_nominal — this is where native tail vs RP-dressed tail shows up."""
    fig, ax = plt.subplots(figsize=(9, 5.2))
    g = goals_all.loc[goals_all["goal_horizon"] == GOAL_HORIZON].copy()
    colors = {
        "native_ls_app": "#1f4e79",
        "ls_web_donor": "#2ca02c",
        "rp_app_donor": "#ff7f0e",
        "hybrid_donor": "#9467bd",
        "native_early_rp_tail": "#17becf",
    }
    for method, sub in g.groupby("method", observed=True):
        sub = sub.sort_values("day")
        ax.plot(
            sub["day"],
            sub["ARPU_nominal"],
            label=method,
            color=colors.get(method),
            lw=1.8,
        )
    ax.set_xlabel("Life day D")
    ax.set_ylabel("ARPU_nominal ($)")
    ax.set_title("lonestar · App — frozen ARPU to day 120")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fname = "plot_ls_app_horizon120.png"
    fig.savefig(out_dir / fname, dpi=140)
    plt.close(fig)
    return [fname]


def write_writeup(
    out_dir: Path,
    summary: pd.DataFrame,
    verdict: pd.DataFrame,
    goals_all: pd.DataFrame | None = None,
    splice_day: int | None = None,
) -> None:
    splice_note = (
        f"`native_early_rp_tail` keeps LS App native through day **{splice_day}**, "
        "then dresses RP App day-to-day growth to 120."
        if splice_day is not None
        else "`native_early_rp_tail` = LS App native early + RP App growth in the tail."
    )
    lines = [
        "*Lee Jerusalmy*",
        "",
        "# LS App bootstrap — provisional method compare",
        "",
        f"Launch **{LAUNCH.date()}**. Scored through **{OBS_END.date()}** on LS App users "
        f"with cost_date **{EVAL_START.date()}..{EVAL_END.date()}**.",
        "",
        "Primary = shape so far on a fixed user set: "
        "actual `ARPU(d)/ARPU(D*)` vs candidate `ARPU_nominal(d)/ARPU_nominal(D*)`.",
        "",
        splice_note,
        "",
        "Not a methodology lock.",
        "",
        "## Method ranking (lower shape MAE wins)",
        "",
        "### launch_day (16 Jul only)",
        "",
        "| Rank | Method | Users | D* | Shape MAE | Bias |",
        "|-----:|--------|------:|---:|----------:|-----:|",
    ]
    day_rows = summary.loc[summary["slice"] == SLICE_LAUNCH_DAY]
    for _, r in day_rows.iterrows():
        lines.append(
            f"| {int(r['rank'])} | {r['method']} | {int(r['n_users']):,} | "
            f"{int(r['d_star'])} | {base._fmt_num(r['shape_mae'])} | "
            f"{base._fmt_num(r['shape_bias'])} |"
        )
    lines += [
        "",
        "### launch_week (16–22 Jul)",
        "",
        "| Rank | Method | Users | D* | Shape MAE | Bias |",
        "|-----:|--------|------:|---:|----------:|-----:|",
    ]
    week_rows = summary.loc[summary["slice"] == SLICE_LAUNCH_WEEK]
    for _, r in week_rows.iterrows():
        lines.append(
            f"| {int(r['rank'])} | {r['method']} | {int(r['n_users']):,} | "
            f"{int(r['d_star'])} | {base._fmt_num(r['shape_mae'])} | "
            f"{base._fmt_num(r['shape_bias'])} |"
        )
    if not verdict.empty:
        best_day = verdict.loc[
            (verdict["slice"] == SLICE_LAUNCH_DAY) & verdict["winner"]
        ]
        if len(best_day):
            best = best_day.iloc[0]
            lines += [
                "",
                f"**Current leader on launch_day:** `{best['method']}` "
                f"(shape MAE {base._fmt_num(best['shape_mae'])}).",
            ]
    if goals_all is not None and not goals_all.empty:
        lines += [
            "",
            "## Frozen ARPU_nominal at checkpoints",
            "",
            "| Method | D1 | D7 | D14 | D30 | D60 | D90 | D120 |",
            "|--------|---:|---:|----:|----:|----:|----:|-----:|",
        ]
        g = goals_all.loc[goals_all["goal_horizon"] == GOAL_HORIZON]
        for method, sub in g.groupby("method", observed=True):
            s = sub.set_index("day")
            cells = []
            for d in HORIZON_DAYS:
                if d in s.index:
                    cells.append(base._fmt_num(s.loc[d, "ARPU_nominal"], 2))
                else:
                    cells.append("—")
            lines.append(f"| {method} | " + " | ".join(cells) + " |")
        lines += [
            "",
            "Short-horizon ranking does not see the tail. Use this table (and "
            "`plot_ls_app_horizon120.png`) for the 120-day goal.",
            "",
            "Re-run as more post-launch cohorts accumulate.",
        ]
    (out_dir / "WRITEUP.md").write_text("\n".join(lines))


def count_eval_users(ns: dict) -> pd.DataFrame:
    cfg = ns["BRAND_CONFIGS"]["lonestar"]
    sql = f"""
    SELECT
      cost_date,
      COUNT(*) AS n_users
    FROM (
      {ls_users_sql(cfg, EVAL_START, EVAL_END)}
    )
    WHERE population = 'App'
    GROUP BY cost_date
    ORDER BY cost_date
    """
    log("[lonestar] count-only LS App eval users")
    out = read_gbq(ns, sql)
    out["cost_date"] = pd.to_datetime(out["cost_date"]).dt.date
    return out


def export_run(
    *,
    goals_all,
    actuals,
    compare_all,
    summary,
    verdict,
    count_df,
    run_ts: str,
    plot_names: list[str],
    splice_day: int | None = None,
) -> Path:
    out_dir = RUNS / f"2026-08-17_ls_app_bootstrap_{run_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    goals_all.to_csv(out_dir / "candidate_goals.csv", index=False)
    actuals.to_csv(out_dir / "actuals_daily.csv", index=False)
    compare_all.to_csv(out_dir / "compare_daily.csv", index=False)
    summary.to_csv(out_dir / "method_summary.csv", index=False)
    verdict.to_csv(out_dir / "method_verdict.csv", index=False)
    count_df.to_csv(out_dir / "eval_user_counts.csv", index=False)
    milestones = compare_all.loc[compare_all["day"].isin(CHECKPOINTS)].copy()
    milestones.to_csv(out_dir / "compare_milestones.csv", index=False)
    meta = pd.DataFrame(
        [
            dict(
                launch=str(LAUNCH.date()),
                freeze=str(FREEZE.date()),
                obs_end=str(OBS_END.date()),
                eval_start=str(EVAL_START.date()),
                eval_end=str(EVAL_END.date()),
                goal_horizon=GOAL_HORIZON,
                primary="shape_to_dstar",
                methods=";".join(METHODS),
                splice_day=splice_day,
                run_ts=run_ts,
                exported_at=datetime.now().isoformat(timespec="seconds"),
                plots=";".join(plot_names),
            )
        ]
    )
    meta.to_csv(out_dir / "run_meta.csv", index=False)
    label = (
        "*Lee Jerusalmy*\n\n"
        "# LS App bootstrap compare\n\n"
        f"Launch **{LAUNCH.date()}**, scored through **{OBS_END.date()}**. "
        "Provisional only — not a methodology lock.\n"
    )
    (out_dir / "LABEL.md").write_text(label)
    write_writeup(
        out_dir,
        summary,
        verdict,
        goals_all=goals_all,
        splice_day=splice_day,
    )
    log(f"exported {out_dir}")
    return out_dir


def run_pipeline_for_brand(ns: dict, brand_key: str, train_users, train_rev) -> dict:
    cfg = ns["BRAND_CONFIGS"][brand_key]
    ns["apply_brand_globals"](cfg)
    log(f"[{cfg['brand']}] pipeline as_of={FREEZE.date()}")
    return ns["run_brand_pipeline"](
        cfg,
        train_users,
        train_rev,
        as_of_date=FREEZE,
        monitor=False,
    )


def build_method_goals(
    ns: dict,
    *,
    ls_result: dict,
    rp_result: dict,
    target_d1: float,
) -> tuple[dict[str, pd.DataFrame], int | None]:
    ls_curve = ls_result["curve"]
    rp_curve = rp_result["curve"]
    organic_df = ls_result["organic"]

    native_curve = curve_for_pop(ls_curve, TARGET_POP)
    tail_curve, splice_day = native_early_rp_tail_curve(native_curve, rp_curve)
    method_curves = {
        "native_ls_app": native_curve,
        "ls_web_donor": scale_donor_curve(
            ls_curve, donor_pop="Web", target_d1=target_d1
        ),
        "rp_app_donor": scale_donor_curve(
            rp_curve, donor_pop="App", target_d1=target_d1
        ),
        "hybrid_donor": hybrid_donor_curve(
            ls_curve, rp_curve, target_d1=target_d1
        ),
        "native_early_rp_tail": tail_curve,
    }

    out = {}
    for method, curve in method_curves.items():
        if curve.empty:
            log(f"[skip] {method}: empty curve")
            continue
        out[method] = goals_from_curve(ns, curve, organic_df, method=method)
        log(f"[ok] {method}: goals rows={len(out[method]):,}")
    return out, splice_day


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count-only", action="store_true", help="Cheap LS App volume check")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh BQ pull")
    args = parser.parse_args(argv)

    if CREDS.is_file():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(CREDS))

    install_calendar()
    ns = load_helpers()

    if args.count_only:
        counts = count_eval_users(ns)
        print(counts.to_string(index=False))
        print(f"\nTotal App users {EVAL_START.date()}..{EVAL_END.date()}: {counts['n_users'].sum():,}")
        return 0

    use_cache = not args.no_cache
    ls_users, ls_rev = load_brand_tables(ns, "lonestar", use_cache=use_cache)
    rp_users, rp_rev = load_brand_tables(ns, "realprize", use_cache=use_cache)

    ls_train_u, ls_train_r, ls_eval_u, ls_eval_r = split_train_eval(ls_users, ls_rev)
    rp_train_u, rp_train_r, _, _ = split_train_eval(rp_users, rp_rev)

    eval_app = ls_eval_u.loc[ls_eval_u["population"] == TARGET_POP].copy()
    launch_day_n = len(eval_slices(eval_app)[SLICE_LAUNCH_DAY])
    log(
        f"eval LS App users={eval_app['id'].nunique():,}  "
        f"launch_day={launch_day_n:,}  "
        f"launch_day_d*={d_star_for_users(eval_slices(eval_app)[SLICE_LAUNCH_DAY])}"
    )
    if eval_app.empty:
        raise RuntimeError("No LS App eval users in launch window.")

    ls_result = run_pipeline_for_brand(ns, "lonestar", ls_train_u, ls_train_r)
    rp_result = run_pipeline_for_brand(ns, "realprize", rp_train_u, rp_train_r)

    target_d1 = app_d1_anchor(ls_result["curve"], ns, ls_train_u, ls_train_r)
    log(f"LS App D1 anchor = ${target_d1:.4f}")

    method_goals, splice_day = build_method_goals(
        ns,
        ls_result=ls_result,
        rp_result=rp_result,
        target_d1=target_d1,
    )
    if not method_goals:
        raise RuntimeError("No method goals built.")

    actuals = build_actuals(ns, eval_app, ls_eval_r)
    compare_parts = []
    goals_parts = []
    for method, goals in method_goals.items():
        goals_parts.append(goals)
        for sl, act_slice in actuals.groupby("slice", observed=True):
            compare_parts.append(compare_method(goals, act_slice))
    goals_all = pd.concat(goals_parts, ignore_index=True)
    compare_all = pd.concat(compare_parts, ignore_index=True)
    summary = method_summary(compare_all)
    verdict = compare_methods(summary)

    run_ts = datetime.now().strftime("%H%M%S")
    out_dir = RUNS / f"2026-08-17_ls_app_bootstrap_{run_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    plots = plot_methods(compare_all, out_dir)
    plots += plot_horizon_levels(goals_all, out_dir)
    counts = (
        eval_app.groupby("cost_date", observed=True)["id"]
        .nunique()
        .reset_index(name="n_users")
    )
    export_run(
        goals_all=goals_all,
        actuals=actuals,
        compare_all=compare_all,
        summary=summary,
        verdict=verdict,
        count_df=counts,
        run_ts=run_ts,
        plot_names=plots,
        splice_day=splice_day,
    )

    print("\nMethod ranking:")
    print(
        summary[
            ["slice", "rank", "method", "n_users", "d_star", "shape_mae", "shape_bias"]
        ].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
