#!/usr/bin/env python3
"""Freeze H=120 goals at 2026-07-10; score available life days through 2026-08-17.

Two engines: production Combined, and capped winsor_escalation (pct_used wired).
Day 120 is not complete — primary is shape so far on a fixed user set.
Does not change generic Combined or DECISIONS.md.
"""
from __future__ import annotations

import argparse
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
APRIL = MG_ROOT / "experiments" / "goal120_realized_2026-04-10"
sys.path.insert(0, str(APRIL))

import run_goal120_realized as base  # noqa: E402
import run_goal120_winsor_esc as esc  # noqa: E402

FREEZE = pd.Timestamp("2026-07-10").normalize()
EVAL_START = pd.Timestamp("2026-07-10").normalize()
OBS_END = pd.Timestamp("2026-08-17").normalize()
EVAL_END = OBS_END
FIRST5_END = pd.Timestamp("2026-07-14").normalize()
CACHE = MG_ROOT / "experiments" / "cache" / "goal120_realized_2026-07-10"
SHAPE_MILESTONES = (1, 7, 14, 30)

SLICE_FIRST = "first_day"
SLICE_FIRST5 = "first_5_days"
SLICE_LEVEL = "overall_level"
PRIMARY_SLICE = SLICE_FIRST


def log(msg: str) -> None:
    base.log(msg)


def days_lived(cost_date, obs_end) -> int:
    return (pd.Timestamp(obs_end).date() - pd.Timestamp(cost_date).date()).days + 1


def install_calendar() -> None:
    """Point the April helpers at this freeze / pull window."""
    base.FREEZE_AS_OF = FREEZE
    base.EVAL_START = EVAL_START
    base.EVAL_END = EVAL_END
    base.EVAL_DEPOSIT_END = OBS_END
    base.SQL_FLOOR = (
        FREEZE - pd.Timedelta(days=base.GOAL_HORIZON + base.LOOKBACK_COHORTS + 5)
    ).normalize()
    base.CACHE = CACHE
    base.MILESTONE_DAYS = SHAPE_MILESTONES
    log(
        f"calendar: freeze={FREEZE.date()}  eval={EVAL_START.date()}..{EVAL_END.date()}  "
        f"obs_end={OBS_END.date()}  sql_floor={base.SQL_FLOOR.date()}  "
        f"max life days (10 Jul)={days_lived(FREEZE, OBS_END)}"
    )


def d_star_for_users(users: pd.DataFrame) -> int:
    if users.empty:
        return 0
    lived = users["cost_date"].map(lambda c: days_lived(c, OBS_END))
    return int(lived.min())


def realized_equal_n(ns, users_slice, revenue_df, *, population: str) -> pd.DataFrame:
    """Same N every day, only through the shortest life in the slice."""
    d_star = d_star_for_users(users_slice)
    if d_star < 1:
        return pd.DataFrame()
    out = base.realized_arpu_path(
        ns, users_slice, revenue_df, population=population, max_day=d_star
    )
    if out.empty:
        return out
    out = out.rename(columns={"actual_arpu_120": "actual_arpu_dstar"})
    out["d_star"] = d_star
    out["shape_ok"] = True
    return out


def realized_mature_level(ns, users_slice, revenue_df, *, population: str) -> pd.DataFrame:
    """One row per day; N = users who have already lived that day. Level only."""
    if users_slice.empty:
        return pd.DataFrame()
    build = ns["build_user_revenue_cums"]
    sum_cum = ns["sum_cum_at_idx"]
    u_in = users_slice.copy()
    u_in["population"] = population
    u_in["cost_date"] = base._norm_cost(u_in["cost_date"])
    max_d = int(u_in["cost_date"].map(lambda c: days_lived(c, OBS_END)).max())
    u_base, daily = build(u_in, revenue_df, max_day=max_d)
    if u_base.empty:
        return pd.DataFrame()
    u_base = u_base.copy()
    u_base["cost_date"] = base._norm_cost(u_base["cost_date"])
    u_base["days_lived"] = u_base["cost_date"].map(lambda c: days_lived(c, OBS_END))
    rows = []
    for day in range(1, max_d + 1):
        cohort = u_base.loc[u_base["days_lived"] >= day]
        n_users = int(cohort["__uid__"].nunique())
        if n_users == 0:
            continue
        keep = cohort[["population", "cost_date", "__uid__"]]
        sums = sum_cum(daily, cohort_users=keep, idx=day - 1, caps=None)
        total = float(sums["sum_cum"].sum()) if len(sums) else 0.0
        rows.append(
            dict(
                population=population,
                day=day,
                n_users=n_users,
                n_cost_dates=int(cohort["cost_date"].nunique()),
                sum_cum=total,
                actual_arpu=total / n_users,
                actual_ratio=np.nan,
                actual_arpu_dstar=np.nan,
                d_star=np.nan,
                shape_ok=False,
            )
        )
    return pd.DataFrame(rows)


def build_actuals(ns, brand: str, eval_users, eval_rev, curve_pops) -> pd.DataFrame:
    eval_users = eval_users.copy()
    eval_users["cost_date"] = base._norm_cost(eval_users["cost_date"])
    first = FREEZE.date()
    first5 = set(pd.date_range(FREEZE, FIRST5_END, freq="D").date)
    slices = {
        SLICE_FIRST: eval_users.loc[eval_users["cost_date"] == first],
        SLICE_FIRST5: eval_users.loc[eval_users["cost_date"].isin(first5)],
        SLICE_LEVEL: eval_users,
    }
    frames = []
    pops = list(curve_pops) + ["Blended"]
    for pop in pops:
        for slice_name, u_all in slices.items():
            if pop == "Blended":
                u_pop = u_all
            else:
                u_pop = u_all.loc[u_all["population"] == pop]
            if u_pop.empty:
                continue
            if slice_name == SLICE_LEVEL:
                path = realized_mature_level(ns, u_pop, eval_rev, population=pop)
            else:
                path = realized_equal_n(ns, u_pop, eval_rev, population=pop)
            if path.empty:
                continue
            path.insert(0, "brand", brand)
            path.insert(2, "slice", slice_name)
            frames.append(path)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def compare_paths(frozen_goals: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    g = frozen_goals.loc[frozen_goals["goal_horizon"] == base.GOAL_HORIZON].copy()
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
    m = actuals.merge(g[keep], on=["brand", "population", "day"], how="left")
    parts = []
    for (_, _, sl), sub in m.groupby(["brand", "population", "slice"], observed=True):
        sub = sub.sort_values("day").copy()
        shape_ok = bool(sub["shape_ok"].iloc[0]) if "shape_ok" in sub.columns else False
        if shape_ok:
            d_star = int(sub["d_star"].iloc[0])
            act_end = float(sub.loc[sub["day"] == d_star, "actual_arpu"].iloc[0])
            frz_end = float(sub.loc[sub["day"] == d_star, "ARPU_nominal"].iloc[0])
            if np.isfinite(act_end) and act_end != 0:
                sub["actual_ratio"] = sub["actual_arpu"] / act_end
            else:
                sub["actual_ratio"] = np.nan
            if np.isfinite(frz_end) and frz_end != 0:
                sub["frozen_shape"] = sub["ARPU_nominal"] / frz_end
            else:
                sub["frozen_shape"] = np.nan
            sub["shape_signed_bias"] = sub["actual_ratio"] - sub["frozen_shape"]
            sub["shape_ae"] = sub["shape_signed_bias"].abs()
            sub["shape_ape"] = base.ape(sub["shape_ae"], sub["frozen_shape"])
        else:
            sub["frozen_shape"] = np.nan
            sub["shape_signed_bias"] = np.nan
            sub["shape_ae"] = np.nan
            sub["shape_ape"] = np.nan
        sub["level_signed_bias"] = sub["actual_arpu"] - sub["ARPU_nominal"]
        sub["level_ae"] = sub["level_signed_bias"].abs()
        sub["level_ape"] = base.ape(sub["level_ae"], sub["ARPU_nominal"])
        parts.append(sub)
    return pd.concat(parts, ignore_index=True) if parts else m


def milestone_table(compare_df: pd.DataFrame) -> pd.DataFrame:
    keep_days = set(SHAPE_MILESTONES)
    extra = compare_df.loc[compare_df["shape_ok"].eq(True), "d_star"]
    if len(extra):
        keep_days |= set(int(x) for x in extra.dropna().unique())
    return (
        compare_df.loc[compare_df["day"].isin(keep_days)]
        .sort_values(["brand", "population", "slice", "day"])
        .reset_index(drop=True)
    )


def error_summary(compare_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (brand, pop, sl), sub in compare_df.groupby(
        ["brand", "population", "slice"], observed=True
    ):
        sub = sub.sort_values("day")
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

        rec = dict(
            brand=brand,
            population=pop,
            slice=sl,
            n_users=int(sub["n_users"].iloc[0]),
            n_users_last=int(sub["n_users"].iloc[-1]),
            d_star=sub["d_star"].iloc[0] if "d_star" in sub.columns else np.nan,
            shape_ok=bool(sub["shape_ok"].iloc[0]) if "shape_ok" in sub.columns else False,
        )
        rec.update(pack("shape", "shape_ae", "shape_signed_bias", "shape_ape"))
        rec.update(pack("level", "level_ae", "level_signed_bias", "level_ape"))
        rows.append(rec)
    return pd.DataFrame(rows).sort_values(["slice", "brand", "population"]).reset_index(drop=True)


def plot_paths(compare_df: pd.DataFrame, out_dir: Path, *, slice_name: str) -> list[str]:
    written = []
    sub0 = compare_df.loc[compare_df["slice"] == slice_name]
    for (brand, pop), sub in sub0.groupby(["brand", "population"], observed=True):
        sub = sub.sort_values("day")
        if sub.empty or not bool(sub["shape_ok"].iloc[0]):
            continue
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 7.2), sharex=True)
        axes[0].plot(sub["day"], sub["frozen_shape"], label="Frozen shape to D*", color="#1f4e79", lw=2)
        axes[0].plot(sub["day"], sub["actual_ratio"], label="Actual ARPU(d)/ARPU(D*)", color="#c45911", lw=2)
        axes[0].set_ylabel("Ratio to last available day")
        axes[0].set_title(f"{brand} · {pop} · {slice_name} — shape so far")
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
        fname = f"plot_{slice_name}_{brand}_{pop.replace(' ', '_')}.png"
        fig.savefig(out_dir / fname, dpi=140)
        plt.close(fig)
        written.append(fname)
    return written


def write_writeup(out_dir: Path, milestones: pd.DataFrame, summary: pd.DataFrame, *, engine: str) -> None:
    lines = [
        "*Lee Jerusalmy*",
        "",
        f"# Freeze 2026-07-10 vs available actuals through 2026-08-17 ({engine})",
        "",
        "Goals frozen at **2026-07-10**. Scored on life days we already have "
        "(oldest cohort = **39** days). Actuals not winsorized.",
        "",
        "**Primary:** shape so far on `first_day` (10 Jul only, same N every day): "
        "actual `ARPU(d)/ARPU(39)` vs frozen `ARPU_nominal(d)/ARPU_nominal(39)`.",
        "",
        "`first_5_days` (10–14 Jul) is the April-style 5-day wave (D* = 35). "
        "`overall_level` is dollars only — N changes by day, do not use for shape.",
        "",
        "## first_day (10 Jul) — shape so far",
        "",
        "| Brand | Population | Users | D* | Shape MAE | Bias | Day-D* actual $ | Frozen $ at D* |",
        "|-------|------------|------:|---:|----------:|-----:|----------------:|---------------:|",
    ]
    ov = summary.loc[summary["slice"] == SLICE_FIRST]
    for _, r in ov.iterrows():
        d_star = int(r["d_star"]) if pd.notna(r["d_star"]) else 0
        drow = milestones.loc[
            (milestones["brand"] == r["brand"])
            & (milestones["population"] == r["population"])
            & (milestones["slice"] == SLICE_FIRST)
            & (milestones["day"] == d_star)
        ]
        act = float(drow["actual_arpu"].iloc[0]) if len(drow) else np.nan
        frz = float(drow["ARPU_nominal"].iloc[0]) if len(drow) else np.nan
        lines.append(
            f"| {r['brand']} | {r['population']} | {int(r['n_users']):,} | {d_star} | "
            f"{base._fmt_num(r['shape_mae'])} | {base._fmt_num(r['shape_bias'])} | "
            f"{base._fmt_num(act, 2)} | {base._fmt_num(frz, 2)} |"
        )
    lines += [
        "",
        "Bias > 0 means actual pace ran **ahead** of the frozen path (to D*).",
        "",
        "Not a methodology lock.",
        "",
    ]
    (out_dir / "WRITEUP.md").write_text("\n".join(lines))


def export_run(
    *,
    engine: str,
    frozen_goals,
    actuals,
    compare_df,
    milestones,
    summary,
    count_df,
    cv_df,
    run_ts: str,
) -> Path:
    tag = (
        f"2026-07-10_rp_ls_goal120_realized_{run_ts}"
        if engine == "production"
        else f"2026-07-10_rp_ls_goal120_realized_winsor_esc_{run_ts}"
    )
    out_dir = base.RUNS / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    plots = plot_paths(compare_df, out_dir, slice_name=SLICE_FIRST)
    plots += plot_paths(compare_df, out_dir, slice_name=SLICE_FIRST5)
    label = (
        "*Lee Jerusalmy*\n\n"
        f"# 2026-07-10 RP+LS goal check — {engine}\n\n"
        "Frozen H=120 goals as of **2026-07-10**, scored through **2026-08-17**. "
        "Primary = shape so far on 10 Jul users (D*=39). Actuals not winsorized. "
        "Not a methodology lock.\n"
    )
    extra = {
        "engine": engine,
        "obs_end": str(OBS_END.date()),
        "primary_slice": PRIMARY_SLICE,
        "primary": "shape_to_dstar",
        "max_life_days_first": days_lived(FREEZE, OBS_END),
        "pct_used_wired_into_curve": engine != "production",
    }
    base.write_export(
        out_dir,
        frozen_goals=frozen_goals,
        actuals=actuals,
        compare_df=compare_df,
        milestones=milestones,
        summary=summary,
        count_df=count_df,
        plot_names=plots,
        run_ts=run_ts,
        extra_meta=extra,
        label_md=label,
        write_writeup_fn=lambda d, ms, sm: write_writeup(d, ms, sm, engine=engine),
    )
    if cv_df is not None and len(cv_df):
        cv_df.to_csv(out_dir / "cv_patches.csv", index=False)
    log(f"exported {out_dir}")
    return out_dir


def compare_engines(prod_sum: pd.DataFrame, esc_sum: pd.DataFrame) -> pd.DataFrame:
    keys = ["brand", "population", "slice"]
    a = prod_sum[keys + ["n_users", "d_star", "shape_mae", "shape_bias", "level_mae", "level_bias"]].copy()
    b = esc_sum[keys + ["shape_mae", "shape_bias", "level_mae", "level_bias"]].copy()
    a = a.rename(
        columns={
            "shape_mae": "prod_shape_mae",
            "shape_bias": "prod_shape_bias",
            "level_mae": "prod_level_mae",
            "level_bias": "prod_level_bias",
        }
    )
    b = b.rename(
        columns={
            "shape_mae": "esc_shape_mae",
            "shape_bias": "esc_shape_bias",
            "level_mae": "esc_level_mae",
            "level_bias": "esc_level_bias",
        }
    )
    m = a.merge(b, on=keys, how="outer")
    m["shape_mae_delta"] = m["esc_shape_mae"] - m["prod_shape_mae"]
    m["shape_winner"] = np.where(
        m["esc_shape_mae"].isna() | m["prod_shape_mae"].isna(),
        "",
        np.where(
            np.isclose(m["esc_shape_mae"], m["prod_shape_mae"]),
            "tie",
            np.where(m["esc_shape_mae"] < m["prod_shape_mae"], "winsor_esc", "production"),
        ),
    )
    return m.sort_values(["slice", "brand", "population"]).reset_index(drop=True)


def load_helpers(engine: str) -> dict:
    ns: dict = {"__name__": f"july_{engine}_helpers"}
    if engine == "production":
        base.exec_combined_helpers(ns)
    else:
        base.exec_combined_helpers(ns, nb_path=esc.WINSOR_NB)
        esc.confirm_capped_engine(ns)
        esc.wire_pct_used_into_curve(ns)
    base.apply_check_calendar(ns)
    return ns


def frozen_for_brands(ns: dict, train_pack: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    frozen_parts, cv_parts = [], []
    for brand_key, (train_u, train_r) in train_pack.items():
        result = base.run_frozen_goals(ns, brand_key, train_u, train_r)
        if result.get("goals") is not None and len(result["goals"]):
            frozen_parts.append(result["goals"])
        if result.get("cv") is not None and len(result["cv"]):
            cv_parts.append(result["cv"])
    frozen = pd.concat(frozen_parts, ignore_index=True) if frozen_parts else pd.DataFrame()
    cv_df = pd.concat(cv_parts, ignore_index=True) if cv_parts else pd.DataFrame()
    return frozen, cv_df


def score_and_export(engine: str, frozen, actuals, count_df, cv_df, run_ts: str) -> tuple[Path, pd.DataFrame]:
    compare_df = compare_paths(frozen, actuals)
    milestones = milestone_table(compare_df)
    summary = error_summary(compare_df)
    out_dir = export_run(
        engine=engine,
        frozen_goals=frozen,
        actuals=actuals,
        compare_df=compare_df,
        milestones=milestones,
        summary=summary,
        count_df=count_df,
        cv_df=cv_df,
        run_ts=run_ts,
    )
    print(f"\n{engine} — first_day shape so far:\n")
    cols = ["brand", "population", "n_users", "d_star", "shape_mae", "shape_bias", "level_mae"]
    print(summary.loc[summary["slice"] == SLICE_FIRST, cols].to_string(index=False))
    return out_dir, summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="H=120 freeze 2026-07-10 vs data through 2026-08-17")
    parser.add_argument(
        "--engine",
        choices=["both", "production", "winsor_esc"],
        default="both",
    )
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args(argv)

    log("=== goal120 July-10 check ===")
    log("primary=shape so far on first_day (D*=39)  actuals not winsorized")
    install_calendar()

    try:
        import google.colab  # noqa: F401
    except ImportError:
        base.setup_local_creds()

    ns_prod = load_helpers("production")
    count_df = base.count_eval_users(ns_prod)
    print("\nEval user counts (cost_date 2026-07-10..08-17):\n")
    print(count_df.to_string(index=False))
    print()
    if args.count_only:
        log("count-only — stop")
        return 0

    train_pack = {}
    actual_parts = []
    for brand_key in ns_prod["RUN_BRANDS"]:
        cfg = ns_prod["BRAND_CONFIGS"][brand_key]
        brand = cfg["brand"]
        users_df, revenue_df = base.load_narrow_tables(ns_prod, cfg, use_cache=not args.no_cache)
        train_u, train_r, eval_u, eval_r = base.split_train_eval(users_df, revenue_df)
        log(
            f"[{brand}] train users={len(train_u):,}  eval users={len(eval_u):,}  "
            f"train rev rows={len(train_r):,}"
        )
        train_pack[brand_key] = (train_u, train_r)
        actuals_b = build_actuals(ns_prod, brand, eval_u, eval_r, cfg["populations"])
        log(f"[{brand}] actual rows={len(actuals_b):,}")
        actual_parts.append(actuals_b)
    actuals = pd.concat(actual_parts, ignore_index=True) if actual_parts else pd.DataFrame()
    if actuals.empty:
        log("ERROR: no actuals")
        return 1

    run_ts = datetime.now().strftime("%H%M%S")
    engines = ["production", "winsor_esc"] if args.engine == "both" else [args.engine]
    summaries = {}
    out_dirs = {}

    if "production" in engines:
        frozen, cv_df = frozen_for_brands(ns_prod, train_pack)
        if frozen.empty:
            log("ERROR: no production frozen goals")
            return 1
        out_dirs["production"], summaries["production"] = score_and_export(
            "production", frozen, actuals, count_df, cv_df, run_ts
        )

    if "winsor_esc" in engines:
        ns_esc = load_helpers("winsor_esc")
        frozen, cv_df = frozen_for_brands(ns_esc, train_pack)
        if frozen.empty:
            log("ERROR: no winsor_esc frozen goals")
            return 1
        out_dirs["winsor_esc"], summaries["winsor_esc"] = score_and_export(
            "winsor_esc", frozen, actuals, count_df, cv_df, run_ts
        )

    if "production" in summaries and "winsor_esc" in summaries:
        vs = compare_engines(summaries["production"], summaries["winsor_esc"])
        vs_path = out_dirs["winsor_esc"] / "compare_vs_production.csv"
        vs.to_csv(vs_path, index=False)
        print("\nShape so far — production vs winsor_esc (first_day):\n")
        show = vs.loc[
            vs["slice"] == SLICE_FIRST,
            [
                "brand",
                "population",
                "n_users",
                "d_star",
                "prod_shape_mae",
                "esc_shape_mae",
                "shape_mae_delta",
                "shape_winner",
            ],
        ]
        print(show.to_string(index=False))
        log(f"engine compare {vs_path}")
    return 0


if __name__ == "__main__":
    rc = main()
    try:
        get_ipython()
    except NameError:
        sys.exit(rc)
