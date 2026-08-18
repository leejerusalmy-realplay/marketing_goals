#!/usr/bin/env python3
"""Same 2026-04-10 H=120 freeze check, frozen goals from capped winsor_escalation.

Capped version: escalate winsor toward cv_threshold; stop if revenue cut > 15%
(absolute). Helpers from experiments/cv_optimization/winsor_escalation/
Marketing_Goals_Combined_RP_LS_Colab.ipynb.

The archived notebook still builds curve day-steps on config-floor winsor
(`pct_used` not wired). This check copy wires pct_used into the curve so the
comparison is actually about different goals. Does not change generic Combined,
the archived experiment notebook, or DECISIONS.md.

Same freeze / eval dates / actuals as run_goal120_realized.py.
"""
from __future__ import annotations

import argparse
import inspect
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_goal120_realized as base  # noqa: E402

WINSOR_NB = (
    base.MG_ROOT
    / "experiments"
    / "cv_optimization"
    / "winsor_escalation"
    / "Marketing_Goals_Combined_RP_LS_Colab.ipynb"
)
BASELINE_DIR = base.MG_ROOT / "runs" / "2026-04-10_rp_ls_goal120_realized_133457"
MAX_REV_CUT_EXPECTED = 0.15
EXPORT_PREFIX = "2026-04-10_rp_ls_goal120_realized_winsor_esc"


def log(msg: str) -> None:
    base.log(msg)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(base.MG_ROOT))
    except ValueError:
        return str(path)


def confirm_capped_engine(ns: dict) -> None:
    """Refuse the uncapped notebook / a missing revenue stop."""
    cut = ns.get("MAX_REVENUE_CUT_FRACTION")
    steps = ns.get("WINSOR_ESCALATION_STEPS")
    if cut is None:
        raise RuntimeError(
            "MAX_REVENUE_CUT_FRACTION missing — this is not the capped "
            "winsor_escalation notebook."
        )
    if abs(float(cut) - MAX_REV_CUT_EXPECTED) > 1e-12:
        raise RuntimeError(
            f"MAX_REVENUE_CUT_FRACTION={cut!r}; expected {MAX_REV_CUT_EXPECTED} "
            "(absolute revenue-cut stop)."
        )
    if not steps:
        raise RuntimeError("WINSOR_ESCALATION_STEPS missing.")
    sig = inspect.signature(ns["get_trimmed_cohort_and_caps"])
    if "pct_override" not in sig.parameters:
        raise RuntimeError("get_trimmed_cohort_and_caps has no pct_override.")
    log(
        f"engine=capped winsor_escalation  "
        f"MAX_REVENUE_CUT_FRACTION={float(cut):.0%}  "
        f"steps={list(steps)}"
    )


def wire_pct_used_into_curve(ns: dict) -> dict:
    """Curve day-steps + D1 anchor use the pct the CV pass actually kept.

    Check copy only. Archived notebook still calls get_trimmed without
    pct_override on the second pass (config floor).
    """
    orig_patch = ns["patch_cv_adaptive"]
    orig_get = ns["get_trimmed_cohort_and_caps"]
    pct_by_pop_e: dict[tuple, float] = {}

    def patch_cv_adaptive(*args, **kwargs):
        patch, stats, removed, flagged, newly = orig_patch(*args, **kwargs)
        if stats:
            pop = stats.get("population") or kwargs.get("population")
            e = kwargs.get("e")
            if e is None and stats.get("patch"):
                e = int(str(stats["patch"]).split("->")[1])
            if pop is not None and e is not None and "pct_used" in stats:
                pct_by_pop_e[(pop, int(e))] = stats["pct_used"]
        return patch, stats, removed, flagged, newly

    def get_trimmed_cohort_and_caps(
        population, cohort_users, daily_user_cums, e, pct_override=None
    ):
        if pct_override is None:
            pct_override = pct_by_pop_e.get((population, int(e)))
        return orig_get(
            population, cohort_users, daily_user_cums, e, pct_override=pct_override
        )

    ns["patch_cv_adaptive"] = patch_cv_adaptive
    ns["get_trimmed_cohort_and_caps"] = get_trimmed_cohort_and_caps
    ns["_pct_used_by_pop_e"] = pct_by_pop_e
    log("wired pct_used into curve day-steps (this check only)")
    return pct_by_pop_e


def load_baseline_actuals(baseline_dir: Path):
    actuals_path = baseline_dir / "actuals_daily.csv"
    counts_path = baseline_dir / "eval_user_counts.csv"
    if not actuals_path.is_file():
        raise FileNotFoundError(f"No baseline actuals: {actuals_path}")
    actuals = pd.read_csv(actuals_path)
    counts = pd.read_csv(counts_path) if counts_path.is_file() else None
    log(f"reuse actuals from {_rel(baseline_dir)}  rows={len(actuals):,}")
    return actuals, counts


def plot_vs_baseline(compare_df: pd.DataFrame, baseline_dir: Path, out_dir: Path) -> list[str]:
    """Overlay production Combined raw path vs winsor_esc vs actual."""
    base_daily = baseline_dir / "compare_daily.csv"
    if not base_daily.is_file():
        return base.plot_paths(compare_df, out_dir)

    prod = pd.read_csv(base_daily)
    prod = prod.loc[prod["slice"] == "overall", ["brand", "population", "day", "raw_goal_ratio"]]
    prod = prod.rename(columns={"raw_goal_ratio": "prod_raw_goal_ratio"})

    overall = compare_df.loc[compare_df["slice"] == "overall"].copy()
    overall = overall.merge(prod, on=["brand", "population", "day"], how="left")
    written = []
    for (brand, pop), sub in overall.groupby(["brand", "population"], observed=True):
        sub = sub.sort_values("day")
        if sub.empty:
            continue
        fig, axes = plt.subplots(2, 1, figsize=(8.5, 7.2), sharex=True)

        if sub["prod_raw_goal_ratio"].notna().any():
            axes[0].plot(
                sub["day"],
                sub["prod_raw_goal_ratio"],
                label="Production Combined raw",
                color="#7f7f7f",
                lw=1.4,
                ls="--",
            )
        axes[0].plot(
            sub["day"],
            sub["raw_goal_ratio"],
            label="Winsor-esc (capped) raw",
            color="#1f4e79",
            lw=2,
        )
        axes[0].plot(
            sub["day"],
            sub["actual_ratio"],
            label="Actual ARPU(d)/ARPU(120)",
            color="#c45911",
            lw=2,
        )
        axes[0].set_ylabel("Ratio to day 120")
        axes[0].set_title(f"{brand} · {pop} — shape (primary)")
        axes[0].legend(loc="lower right", fontsize=8)
        axes[0].grid(True, alpha=0.25)

        axes[1].plot(
            sub["day"], sub["ARPU_nominal"], label="Winsor-esc ARPU_nominal", color="#1f4e79", lw=2
        )
        axes[1].plot(
            sub["day"], sub["actual_arpu"], label="Actual ARPU (no winsor)", color="#c45911", lw=2
        )
        axes[1].set_xlabel("Life day D  (dsi ≤ D−1)")
        axes[1].set_ylabel("ARPU ($)")
        axes[1].set_title(f"{brand} · {pop} — level (secondary)")
        axes[1].legend(loc="lower right", fontsize=8)
        axes[1].grid(True, alpha=0.25)

        fig.tight_layout()
        fname = f"plot_{brand}_{pop.replace(' ', '_')}.png"
        fig.savefig(out_dir / fname, dpi=140)
        plt.close(fig)
        written.append(fname)
    return written


def compare_engines(baseline_dir: Path, summary: pd.DataFrame, frozen_goals: pd.DataFrame) -> pd.DataFrame:
    prod_sum = pd.read_csv(baseline_dir / "error_summary.csv")
    keep = [
        "brand",
        "population",
        "slice",
        "n_users",
        "shape_mae",
        "shape_median_ae",
        "shape_bias",
        "level_mae",
        "level_bias",
    ]
    keep = [c for c in keep if c in prod_sum.columns]
    a = prod_sum[keep].rename(
        columns={
            c: f"prod_{c}"
            for c in keep
            if c not in ("brand", "population", "slice", "n_users")
        }
    )
    b = summary[keep].rename(
        columns={
            c: f"esc_{c}"
            for c in keep
            if c not in ("brand", "population", "slice", "n_users")
        }
    )
    m = a.merge(b, on=["brand", "population", "slice", "n_users"], how="outer")
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

    prod_g = pd.read_csv(baseline_dir / "frozen_goals_h120.csv")
    prod_h = (
        prod_g.loc[prod_g["goal_horizon"] == base.GOAL_HORIZON, ["brand", "population", "ARPU_at_horizon"]]
        .drop_duplicates(["brand", "population"])
        .rename(columns={"ARPU_at_horizon": "prod_ARPU_120"})
    )
    esc_h = (
        frozen_goals.loc[
            frozen_goals["goal_horizon"] == base.GOAL_HORIZON, ["brand", "population", "ARPU_at_horizon"]
        ]
        .drop_duplicates(["brand", "population"])
        .rename(columns={"ARPU_at_horizon": "esc_ARPU_120"})
    )
    m = m.merge(prod_h, on=["brand", "population"], how="left").merge(
        esc_h, on=["brand", "population"], how="left"
    )
    return m.sort_values(["slice", "brand", "population"]).reset_index(drop=True)


def write_variant_writeup(
    out_dir: Path,
    milestones: pd.DataFrame,
    summary: pd.DataFrame,
    *,
    vs: pd.DataFrame | None,
    cv_df: pd.DataFrame | None,
    baseline_dir: Path | None,
) -> None:
    lines = [
        "*Lee Jerusalmy*",
        "",
        "# Did capped winsor_escalation H=120 goals match Apr 10–14 better?",
        "",
        "Same freeze as the production Combined check: **2026-04-10**, "
        "eval cost_dates **Apr 10–14**, actuals **not** winsorized, primary = **shape**.",
        "",
        "Frozen goals from **capped** `winsor_escalation` (stop if revenue cut > **15%** absolute). "
        "`pct_used` is wired into curve day-steps for this check only — without that, "
        "goals would still sit on floor winsor and the comparison would be empty.",
        "",
        "Not a methodology lock. Does not change generic Combined.",
        "",
        "## Overall (5 dates pooled) — shape error, this engine",
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
            f"{base._fmt_num(r['shape_mae'])} | {base._fmt_num(r['shape_median_ae'])} | "
            f"{base._fmt_num(r['shape_bias'])} | {base._fmt_num(act, 2)} | {base._fmt_num(frz, 2)} |"
        )

    if vs is not None and len(vs):
        lines += [
            "",
            "## Which engine matches better? (primary = shape MAE, overall)",
            "",
            f"Production freeze: `{_rel(baseline_dir)}`." if baseline_dir else "",
            "",
            "| Brand | Pop | Users | Prod MAE | Esc MAE | Δ (esc − prod) | Winner | Prod ARPU_120 | Esc ARPU_120 |",
            "|-------|-----|------:|---------:|--------:|---------------:|--------|--------------:|-------------:|",
        ]
        ov_vs = vs.loc[vs["slice"] == "overall"]
        for _, r in ov_vs.iterrows():
            lines.append(
                f"| {r['brand']} | {r['population']} | {int(r['n_users']):,} | "
                f"{base._fmt_num(r['prod_shape_mae'])} | {base._fmt_num(r['esc_shape_mae'])} | "
                f"{base._fmt_num(r['shape_mae_delta'])} | {r['shape_winner']} | "
                f"{base._fmt_num(r.get('prod_ARPU_120'), 2)} | {base._fmt_num(r.get('esc_ARPU_120'), 2)} |"
            )
        lines += [
            "",
            "Lower shape MAE = closer pace to realized `ARPU(d)/ARPU(120)`. "
            "RP Web is thin (ignore). Affiliate floor 1% already cuts a large $ share, "
            "so those patches can show `capped_by_revenue_limit` even without climbing the ladder.",
        ]

    if cv_df is not None and len(cv_df):
        cols = [
            c
            for c in [
                "brand",
                "population",
                "patch",
                "floor_pct",
                "pct_used",
                "escalated",
                "revenue_cut_fraction",
                "capped_by_revenue_limit",
                "cv_before",
                "cv_after",
                "flagged",
            ]
            if c in cv_df.columns
        ]
        show = cv_df[cols].copy() if cols else cv_df
        lines += [
            "",
            "## Freeze-T CV / winsor (patches through 120)",
            "",
            "| " + " | ".join(cols) + " |",
            "|" + "|".join(["---"] * len(cols)) + "|",
        ]
        for _, r in show.iterrows():
            cells = []
            for c in cols:
                v = r[c]
                if c in ("floor_pct", "pct_used", "revenue_cut_fraction", "cv_before", "cv_after"):
                    cells.append(base._fmt_num(v, 3) if pd.notna(v) else "—")
                else:
                    cells.append(str(v))
            lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "## How to read this",
        "",
        "- **Shape (primary):** did realized *pace* to day 120 match the frozen raw path?",
        "- Same actuals as the production freeze (raw ARPU; $0 users in N).",
        "- Adjusted sits below actual ratio by ~organic, by design. Not the verdict.",
        "",
        "Not a methodology lock.",
        "",
    ]
    (out_dir / "WRITEUP.md").write_text("\n".join(lines))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="H=120 freeze 2026-04-10 using capped winsor_escalation goals"
    )
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument(
        "--no-reuse-actuals",
        action="store_true",
        help="Recompute Apr 10–14 actuals instead of reusing the production freeze file",
    )
    parser.add_argument(
        "--baseline-dir",
        default=str(BASELINE_DIR),
        help="Production freeze export to compare against",
    )
    args = parser.parse_args(argv)
    baseline_dir = Path(args.baseline_dir)

    log("=== goal120 realized check · capped winsor_escalation ===")
    log(f"freeze={base.FREEZE_AS_OF.date()}  eval={base.EVAL_START.date()}..{base.EVAL_END.date()}")
    log(f"notebook={_rel(WINSOR_NB)}")
    log("primary=shape  actuals not winsorized  pct_used wired into curve")

    try:
        import google.colab  # noqa: F401

        in_colab = True
    except ImportError:
        in_colab = False
    if not in_colab:
        base.setup_local_creds()

    ns: dict = {"__name__": "winsor_esc_helpers"}
    base.exec_combined_helpers(ns, nb_path=WINSOR_NB)
    confirm_capped_engine(ns)
    wire_pct_used_into_curve(ns)
    base.apply_check_calendar(ns)

    reuse_actuals = (not args.no_reuse_actuals) and (baseline_dir / "actuals_daily.csv").is_file()
    if args.count_only and not reuse_actuals:
        count_df = base.count_eval_users(ns)
        print("\nEval user counts (cost_date 2026-04-10..14):\n")
        print(count_df.to_string(index=False))
        log("count-only — stop")
        return 0

    if reuse_actuals:
        actuals, count_df = load_baseline_actuals(baseline_dir)
        if args.count_only:
            if count_df is not None:
                print("\nEval user counts (from production freeze):\n")
                print(count_df.to_string(index=False))
            log("count-only — stop")
            return 0
    else:
        count_df = base.count_eval_users(ns)
        print("\nEval user counts (cost_date 2026-04-10..14):\n")
        print(count_df.to_string(index=False))
        print()
        if args.count_only:
            log("count-only — stop")
            return 0

    frozen_parts = []
    cv_parts = []
    actual_parts = []
    for brand_key in ns["RUN_BRANDS"]:
        cfg = ns["BRAND_CONFIGS"][brand_key]
        brand = cfg["brand"]
        users_df, revenue_df = base.load_narrow_tables(ns, cfg, use_cache=not args.no_cache)
        train_u, train_r, eval_u, eval_r = base.split_train_eval(users_df, revenue_df)
        log(
            f"[{brand}] train users={len(train_u):,}  eval users={len(eval_u):,}  "
            f"train rev rows={len(train_r):,}"
        )
        result = base.run_frozen_goals(ns, brand_key, train_u, train_r)
        goals = result["goals"]
        if goals is None or goals.empty:
            log(f"[{brand}] WARNING: no frozen goals")
        else:
            frozen_parts.append(goals)
        if result.get("cv") is not None and len(result["cv"]):
            cv_parts.append(result["cv"])
        if not reuse_actuals:
            actuals_b = base.build_actuals(ns, brand, eval_u, eval_r, cfg["populations"])
            log(f"[{brand}] actual rows={len(actuals_b):,}")
            actual_parts.append(actuals_b)

    frozen_goals = pd.concat(frozen_parts, ignore_index=True) if frozen_parts else pd.DataFrame()
    cv_df = pd.concat(cv_parts, ignore_index=True) if cv_parts else pd.DataFrame()
    if not reuse_actuals:
        actuals = pd.concat(actual_parts, ignore_index=True) if actual_parts else pd.DataFrame()
    if frozen_goals.empty or actuals.empty:
        log("ERROR: missing frozen goals or actuals — no export")
        return 1

    compare_df = base.compare_paths(frozen_goals, actuals)
    milestones = base.milestone_table(compare_df)
    summary = base.error_summary(compare_df)

    vs = None
    if (baseline_dir / "error_summary.csv").is_file():
        vs = compare_engines(baseline_dir, summary, frozen_goals)

    run_ts = datetime.now().strftime("%H%M%S")
    out_dir = base.RUNS / f"{EXPORT_PREFIX}_{run_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if (baseline_dir / "compare_daily.csv").is_file():
        plot_names = plot_vs_baseline(compare_df, baseline_dir, out_dir)
    else:
        plot_names = base.plot_paths(compare_df, out_dir)

    def _writeup(d, ms, sm):
        write_variant_writeup(
            d, ms, sm, vs=vs, cv_df=cv_df, baseline_dir=baseline_dir
        )

    base.write_export(
        out_dir,
        frozen_goals=frozen_goals,
        actuals=actuals,
        compare_df=compare_df,
        milestones=milestones,
        summary=summary,
        count_df=count_df,
        plot_names=plot_names,
        run_ts=run_ts,
        extra_meta={
            "engine": "winsor_escalation_capped",
            "max_revenue_cut_fraction": MAX_REV_CUT_EXPECTED,
            "pct_used_wired_into_curve": True,
            "helpers_notebook": _rel(WINSOR_NB),
            "baseline_run": _rel(baseline_dir) if baseline_dir.exists() else "",
            "reused_actuals": bool(reuse_actuals),
        },
        label_md=(
            "*Lee Jerusalmy*\n\n"
            "# 2026-04-10 RP+LS goal-120 realized check — capped winsor_escalation\n\n"
            "Same freeze/eval as the production Combined check. "
            "Frozen goals from **capped** winsor_escalation (revenue cut stop 15% absolute). "
            "`pct_used` wired into the curve for this check only. "
            "Primary = shape. Actuals not winsorized. Not a methodology lock.\n"
        ),
        write_writeup_fn=_writeup,
    )
    if len(cv_df):
        cv_df.to_csv(out_dir / "cv_patches.csv", index=False)
    if vs is not None:
        vs.to_csv(out_dir / "compare_vs_production.csv", index=False)

    log(f"exported {out_dir}")
    print("\nOverall shape summary (winsor_esc):\n")
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
    if vs is not None:
        print("\nShape MAE vs production Combined freeze:\n")
        show = vs.loc[
            vs["slice"] == "overall",
            [
                "brand",
                "population",
                "n_users",
                "prod_shape_mae",
                "esc_shape_mae",
                "shape_mae_delta",
                "shape_winner",
            ],
        ]
        print(show.to_string(index=False))
    return 0


if __name__ == "__main__":
    rc = main()
    try:
        get_ipython()  # Colab / IPython — do not SystemExit
    except NameError:
        sys.exit(rc)
