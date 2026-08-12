#!/usr/bin/env python3
"""Fast CV flag experiments on cached growth-by-date series.

Phase 1: build_all_patch_series (one BQ/cache pass) → parquet of growth rows.
Phase 2: replay CV knobs (instant) + rebuild selected curves for goal spot-check.
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

# Import helpers from sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_knob_replay import (
    AS_OF, BRAND_CONFIGS, CACHE, CREDS, LOOKBACK, PATCHES, PROJECT,
    build_user_revenue_cums, get_or_cache_brand, get_trimmed_cohort_and_caps,
    sum_cum_at_idx, weighted_mean_std_cv, resolve_max_remove_fraction,
    best_date_by_cv_drop, rank_candidates, build_curve_exp, extrapolate_curve_tail,
    raw_goal_at, arpu_at,
)

SERIES_PATH = CACHE / "patch_growth_series.parquet"
OUT = Path(__file__).resolve().parent / "cv_results_2026-08-03"
OUT.mkdir(parents=True, exist_ok=True)


def build_one_patch_series(u_base, daily, population, s, e, as_of, trim_config):
    as_of = pd.to_datetime(as_of).normalize()
    cohort_end = (as_of - pd.Timedelta(days=e)).date()
    cohort_start = (as_of - pd.Timedelta(days=e + (LOOKBACK - 1))).date()
    cohort_users = u_base.loc[
        (u_base["population"] == population)
        & (u_base["cost_date"] >= cohort_start)
        & (u_base["cost_date"] <= cohort_end)
    ][["population", "cost_date", "__uid__"]].copy()
    if cohort_users.empty:
        return pd.DataFrame()
    trimmed, caps = get_trimmed_cohort_and_caps(
        population, cohort_users, daily, e, trim_config
    )
    denom_w = (
        trimmed.groupby(["population", "cost_date"], observed=True)["__uid__"]
        .nunique()
        .reset_index(name="N_users")
    )
    sum_s = sum_cum_at_idx(daily, cohort_users=trimmed, idx=s - 1, caps=caps).rename(
        columns={"sum_cum": "sum_cum_s"}
    )
    sum_e = sum_cum_at_idx(daily, cohort_users=trimmed, idx=e - 1, caps=caps).rename(
        columns={"sum_cum": "sum_cum_e"}
    )
    patch = denom_w.merge(sum_s, on=["population", "cost_date"]).merge(
        sum_e, on=["population", "cost_date"]
    )
    patch["ARPU_s"] = patch["sum_cum_s"] / patch["N_users"]
    patch["ARPU_e"] = patch["sum_cum_e"] / patch["N_users"]
    patch["growth_ratio"] = np.where(
        patch["ARPU_s"] > 0, patch["ARPU_e"] / patch["ARPU_s"], np.nan
    )
    patch["s"] = s
    patch["e"] = e
    patch["patch"] = f"{s}->{e}"
    return patch


def build_all_series():
    if SERIES_PATH.exists():
        print(f"load series cache {SERIES_PATH}")
        return pd.read_parquet(SERIES_PATH)
    rows = []
    for brand_key, cfg in BRAND_CONFIGS.items():
        print(f"=== building series {brand_key} ===")
        t0 = time.time()
        users, rev = get_or_cache_brand(brand_key)
        # sanitize date types from parquet dbdate
        users = users.copy()
        rev = rev.copy()
        users["cost_date"] = pd.to_datetime(users["cost_date"]).dt.date
        rev["date"] = pd.to_datetime(rev["date"]).dt.date
        pops = list(cfg["populations"]) + ["Blended"]
        for pop in pops:
            print(f"  pop {pop}...")
            if pop == "Blended":
                ub = users.copy()
                ub["population"] = "Blended"
            else:
                ub = users.loc[users["population"] == pop].copy()
            u_base, daily = build_user_revenue_cums(ub, rev, max_day=365)
            for s, e in PATCHES:
                p = build_one_patch_series(
                    u_base, daily, "Blended" if pop == "Blended" else pop,
                    s, e, AS_OF, cfg["trim_config"],
                )
                if p.empty:
                    continue
                # min cohort dates gate
                if len(p) < cfg["min_cohort_dates"]:
                    continue
                p.insert(0, "brand", brand_key)
                rows.append(p)
        print(f"  {brand_key} done in {time.time()-t0:.1f}s")
    out = pd.concat(rows, ignore_index=True)
    # store cost_date as string for parquet safety
    out["cost_date"] = out["cost_date"].astype(str)
    out.to_parquet(SERIES_PATH, index=False)
    print(f"wrote {SERIES_PATH} rows={len(out)} patches={out.groupby(['brand','population','patch']).ngroups}")
    return out


def adaptive_cv_on_series(patch_df, *, cv_threshold, cv_good_enough, max_remove_fraction,
                          rank_mode="abs_dev", stop_at="good_enough"):
    """Return mean_after, cv_before, cv_after, flagged, kept, removed list."""
    g = patch_df["growth_ratio"].values
    w = patch_df["sum_cum_s"].values
    _, _, cv_before = weighted_mean_std_cv(g, w)
    remaining = patch_df.copy()
    max_removable = max(1, int(np.floor(len(remaining) * max_remove_fraction)))
    stop_target = cv_good_enough if stop_at == "good_enough" else cv_threshold
    removed = []
    if rank_mode == "greedy_cv_drop":
        while True:
            _, _, cv_now = weighted_mean_std_cv(
                remaining["growth_ratio"].values, remaining["sum_cum_s"].values
            )
            if np.isnan(cv_now) or cv_now <= stop_target:
                break
            if len(removed) >= max_removable:
                break
            d = best_date_by_cv_drop(remaining)
            if d is None:
                break
            removed.append(d)
            remaining = remaining.loc[~remaining["cost_date"].isin(removed)]
    else:
        sorted_dates = rank_candidates(remaining, rank_mode)
        for candidate in sorted_dates:
            _, _, cv_now = weighted_mean_std_cv(
                remaining["growth_ratio"].values, remaining["sum_cum_s"].values
            )
            if np.isnan(cv_now) or cv_now <= stop_target:
                break
            if len(removed) >= max_removable:
                break
            removed.append(candidate)
            remaining = remaining.loc[~remaining["cost_date"].isin(removed)]
    mean_a, _, cv_after = weighted_mean_std_cv(
        remaining["growth_ratio"].values, remaining["sum_cum_s"].values
    )
    flagged = (not np.isnan(cv_after)) and (cv_after > cv_threshold)
    return dict(
        cv_before=float(cv_before) if not np.isnan(cv_before) else None,
        cv_after=float(cv_after) if not np.isnan(cv_after) else None,
        mean_after=float(mean_a) if not np.isnan(mean_a) else None,
        flagged=bool(flagged),
        n_cohort_dates_total=int(len(patch_df)),
        n_cohort_dates_kept=int(len(remaining)),
        removed_dates=removed,
        max_remove_fraction_used=max_remove_fraction,
    )


def max_remove_for(s, e, policy):
    return resolve_max_remove_fraction(s, e, policy)


EXPERIMENTS = {
    "baseline": dict(remove_policy={"base": 0.15}, rank_mode="abs_dev", stop_at="good_enough"),
    "A_early_max25": dict(
        remove_policy={"base": 0.15, "early_max": 0.25,
                       "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)}},
        rank_mode="abs_dev", stop_at="good_enough"),
    "A_early_max30": dict(
        remove_policy={"base": 0.15, "early_max": 0.30,
                       "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)}},
        rank_mode="abs_dev", stop_at="good_enough"),
    "B_greedy_cv": dict(remove_policy={"base": 0.15}, rank_mode="greedy_cv_drop", stop_at="good_enough"),
    "A25+B": dict(
        remove_policy={"base": 0.15, "early_max": 0.25,
                       "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)}},
        rank_mode="greedy_cv_drop", stop_at="good_enough"),
    "C_wdev_early25": dict(
        remove_policy={"base": 0.15, "early_max": 0.25,
                       "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)}},
        rank_mode="weighted_dev", stop_at="good_enough"),
    "D_global_max25": dict(remove_policy={"base": 0.25}, rank_mode="abs_dev", stop_at="good_enough"),
}


def run_flag_exps(series):
    # parse
    series = series.copy()
    series["s"] = series["s"].astype(int)
    series["e"] = series["e"].astype(int)
    keys = series.groupby(["brand", "population", "patch", "s", "e"], sort=False).groups
    all_rows = []
    for exp_name, cfg in EXPERIMENTS.items():
        for (brand, pop, patch, s, e), idx in keys.items():
            pdf = series.loc[idx].copy()
            thr = BRAND_CONFIGS[brand]["cv_threshold"]
            ge = BRAND_CONFIGS[brand]["cv_good_enough"]
            mrf = max_remove_for(s, e, cfg["remove_policy"])
            res = adaptive_cv_on_series(
                pdf, cv_threshold=thr, cv_good_enough=ge,
                max_remove_fraction=mrf, rank_mode=cfg["rank_mode"],
                stop_at=cfg["stop_at"],
            )
            all_rows.append(dict(
                experiment=exp_name, brand=brand, population=pop, patch=patch,
                s=s, e=e, **res
            ))
        print(f"{exp_name}: flags done")
    long = pd.DataFrame(all_rows)
    long.to_csv(OUT / "cv_long_all_exps.csv", index=False)
    return long


def print_report(long):
    print("\n=== FLAG COUNTS ===")
    for exp, g in long.groupby("experiment", sort=False):
        print(f"  {exp:20s}  {int(g['flagged'].sum()):2d}/{len(g)}")

    base_flags = long.loc[(long["experiment"] == "baseline") & (long["flagged"])]
    print("\n=== BASELINE FLAGGED — cv_after / mean / kept by experiment ===")
    cols = ["experiment", "cv_after", "mean_after", "n_cohort_dates_kept", "flagged"]
    for _, bf in base_flags.iterrows():
        sub = long.loc[
            (long["brand"] == bf["brand"])
            & (long["population"] == bf["population"])
            & (long["patch"] == bf["patch"])
        ]
        print(f"\n{bf['brand']}/{bf['population']}/{bf['patch']}  cv_before~{bf['cv_before']:.3f}")
        for _, r in sub.iterrows():
            star = "FLAG" if r["flagged"] else " ok "
            print(f"  {r['experiment']:18s} {star} cv={r['cv_after']:.4f} mean={r['mean_after']:.4f} kept={r['n_cohort_dates_kept']}")

    print("\n=== REMAINING FLAGS PER EXPERIMENT ===")
    for exp, g in long.groupby("experiment", sort=False):
        fl = g.loc[g["flagged"], ["brand", "population", "patch", "cv_after", "n_cohort_dates_kept"]]
        print(f"\n{exp} ({len(fl)} flags)")
        if len(fl):
            print(fl.to_string(index=False))


def spot_goals_for_exps(exp_names):
    """Rebuild curves only for given experiments; spot-check raw goals."""
    rows = []
    for exp_name in exp_names:
        cfg_exp = EXPERIMENTS[exp_name]
        print(f"\n=== rebuild curves for goals: {exp_name} ===")
        for brand_key, cfg in BRAND_CONFIGS.items():
            users, rev = get_or_cache_brand(brand_key)
            users = users.copy(); rev = rev.copy()
            users["cost_date"] = pd.to_datetime(users["cost_date"]).dt.date
            rev["date"] = pd.to_datetime(rev["date"]).dt.date
            pops = list(cfg["populations"])
            u_pop, daily_pop = build_user_revenue_cums(
                users.loc[users["population"].isin(pops)].copy(), rev, max_day=365
            )
            parts = []
            for pop in pops + ["Blended"]:
                if pop == "Blended":
                    ub = users.copy(); ub["population"] = "Blended"
                    u_b, d_b = build_user_revenue_cums(ub, rev, max_day=365)
                    cv_df, curve = build_curve_exp(
                        u_b, d_b, population="Blended", as_of_date=AS_OF,
                        trim_config=cfg["trim_config"],
                        cv_threshold=cfg["cv_threshold"],
                        cv_good_enough=cfg["cv_good_enough"],
                        remove_policy=cfg_exp["remove_policy"],
                        rank_mode=cfg_exp["rank_mode"],
                        min_cohort_dates=cfg["min_cohort_dates"],
                        stop_at=cfg_exp["stop_at"], debug=False,
                    )
                else:
                    cv_df, curve = build_curve_exp(
                        u_pop, daily_pop, population=pop, as_of_date=AS_OF,
                        trim_config=cfg["trim_config"],
                        cv_threshold=cfg["cv_threshold"],
                        cv_good_enough=cfg["cv_good_enough"],
                        remove_policy=cfg_exp["remove_policy"],
                        rank_mode=cfg_exp["rank_mode"],
                        min_cohort_dates=cfg["min_cohort_dates"],
                        stop_at=cfg_exp["stop_at"], debug=False,
                    )
                if not curve.empty and cfg["extrapolate_tail"]:
                    curve = extrapolate_curve_tail(curve, up_to_day=365,
                                                  tail_days=cfg["extrapolation_tail_days"])
                if not curve.empty:
                    curve = curve.copy()
                    curve.insert(0, "brand", brand_key)
                    parts.append(curve)
            if not parts:
                continue
            curve = pd.concat(parts, ignore_index=True)
            for brand, pop, h, d in [
                (brand_key, "Web", 7, 1),
                (brand_key, "Web", 30, 1),
                (brand_key, "Web", 30, 7),
                (brand_key, "Blended", 7, 1),
            ]:
                if brand_key == "realprize" and pop == "Web":
                    pass
                sub = curve.loc[curve["brand"] == brand]
                if pop not in sub["population"].values:
                    continue
                rows.append(dict(
                    experiment=exp_name, brand=brand, population=pop,
                    metric=f"raw_goal_d{d}/h{h}",
                    value=raw_goal_at(sub, pop, h, d),
                ))
                rows.append(dict(
                    experiment=exp_name, brand=brand, population=pop,
                    metric=f"ARPU_d{h}",
                    value=arpu_at(sub, pop, h),
                ))
            if brand_key == "realprize":
                for pop in ("App",):
                    sub = curve.loc[curve["brand"] == brand_key]
                    rows.append(dict(experiment=exp_name, brand=brand_key, population=pop,
                                     metric="raw_goal_d1/h7", value=raw_goal_at(sub, pop, 7, 1)))
                    rows.append(dict(experiment=exp_name, brand=brand_key, population=pop,
                                     metric="ARPU_d7", value=arpu_at(sub, pop, 7)))
        print(f"  {exp_name} goal build done")
    gdf = pd.DataFrame(rows)
    gdf.to_csv(OUT / "spot_goals_compare.csv", index=False)
    # print deltas
    if gdf.empty:
        return
    base = gdf.loc[gdf["experiment"] == "baseline"].set_index(
        ["brand", "population", "metric"]
    )["value"]
    print("\n=== SPOT GOAL / ARPU vs baseline ===")
    for exp in exp_names:
        if exp == "baseline":
            continue
        print(f"-- {exp} --")
        sub = gdf.loc[gdf["experiment"] == exp]
        for _, r in sub.iterrows():
            b = base.get((r["brand"], r["population"], r["metric"]), np.nan)
            if pd.isna(b) or b == 0 or pd.isna(r["value"]):
                continue
            pct = 100 * (r["value"] - b) / b
            print(f"  {r['brand']}/{r['population']}/{r['metric']}: {b:.4f}->{r['value']:.4f} ({pct:+.2f}%)")


def main():
    # fix parquet date types on load of users cache for get_or_cache
    series = build_all_series()
    long = run_flag_exps(series)
    print_report(long)
    # goals only for baseline + best 1-2 by flag count
    counts = long.groupby("experiment")["flagged"].sum().sort_values()
    print("\nflag ranking:", counts.to_dict())
    best = [c for c in counts.index if c != "baseline"][:2]
    spot_goals_for_exps(["baseline"] + best)
    print(f"\noutputs in {OUT}")


if __name__ == "__main__":
    main()
