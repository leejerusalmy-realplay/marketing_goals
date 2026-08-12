#!/usr/bin/env python3
"""
Offline CV-knob experiments against as_of 2026-08-03.
Caches BQ users+revenue once, then replays patch_cv_adaptive variants.

Does NOT edit production notebooks. Flags still keep patches.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "experiments" / "cache" / "2026-08-03"
CREDS = Path(
    "/Users/leejerusalmy/Library/CloudStorage/GoogleDrive-lee@realplayltd.com/"
    "My Drive/lee_project/oceanic-citadel-454608-d2-e116e15558ce.json"
)
PROJECT = "oceanic-citadel-454608-d2"
AS_OF = pd.Timestamp("2026-08-03")
LOOKBACK = 35
PATCHES = (
    (1, 7), (7, 14), (14, 30), (30, 60), (60, 90),
    (90, 120), (120, 150), (150, 180), (180, 270), (270, 365),
)
GOAL_HORIZONS = [7, 30, 60, 90, 120, 150, 180, 210, 240, 270, 365]

BRAND_CONFIGS = {
    "realprize": {
        "brand": "realprize",
        "cost_table": "analytics.realprize_cost_per_user",
        "deposits_table": "realprize.casino_astropay_dmn",
        "exclude_affids": [4313],
        "populations": ["Web", "App", "Affiliate"],
        "trim_config": {
            "App": {"method": "winsor", "pct": 0},
            "Web": {"method": "winsor", "pct": 0.01},
            "Affiliate": {"method": "winsor", "pct": 0.01},
            "Blended": {"method": "winsor", "pct": 0},
        },
        "cv_threshold": 0.15,
        "cv_good_enough": 0.10,
        "max_remove_fraction": 0.15,
        "min_cohort_dates": 1,
        "extrapolate_tail": False,
        "extrapolation_tail_days": 30,
    },
    "lonestar": {
        "brand": "lonestar",
        "cost_table": "analytics.lonestar_cost_per_user",
        "deposits_table": "lonestar.casino_astropay_dmn",
        "exclude_affids": [4866, 7127],
        "populations": ["Web", "Affiliate"],
        "trim_config": {
            "Web": {"method": "winsor", "pct": 0},
            "Affiliate": {"method": "winsor", "pct": 0.01},
            "Blended": {"method": "winsor", "pct": 0},
        },
        "cv_threshold": 0.175,
        "cv_good_enough": 0.10,
        "max_remove_fraction": 0.15,
        "min_cohort_dates": 20,
        "extrapolate_tail": True,
        "extrapolation_tail_days": 30,
    },
}

# ── math / trim helpers (mirror Combined notebook) ─────────────────────


def weighted_mean_std_cv(x, w):
    x = np.asarray(x, dtype=float)
    w = np.asarray(w, dtype=float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[m], w[m]
    if x.size == 0:
        return np.nan, np.nan, np.nan
    mu = np.average(x, weights=w)
    var = np.average((x - mu) ** 2, weights=w)
    sd = np.sqrt(var)
    cv = sd / mu if mu != 0 else np.nan
    return mu, sd, cv


def build_user_revenue_cums(users_df, revenue_df, *, max_day=365):
    u = users_df[["id", "population", "cost_date"]].copy()
    u["population"] = u["population"].astype(str).str.strip()
    u["cost_date"] = pd.to_datetime(u["cost_date"], errors="coerce").dt.date
    u = u.loc[pd.notna(u["cost_date"])].copy()
    u = u.groupby(["population", "id"], as_index=False)["cost_date"].min()
    u = u.rename(columns={"id": "__uid__"})

    r = revenue_df[["playerid", "date", "amount"]].copy()
    r["date"] = pd.to_datetime(r["date"], errors="coerce").dt.date
    r = r.loc[pd.notna(r["date"])].copy()

    rr = r.merge(u, left_on="playerid", right_on="__uid__", how="inner")
    rr["dsi"] = (pd.to_datetime(rr["date"]) - pd.to_datetime(rr["cost_date"])).dt.days
    rr = rr.loc[(rr["dsi"] >= 0) & (rr["dsi"] <= (max_day - 1))].copy()

    daily_user = (
        rr.groupby(["population", "cost_date", "__uid__", "dsi"], observed=True)["amount"]
        .sum()
        .reset_index()
        .sort_values(["population", "cost_date", "__uid__", "dsi"])
    )
    daily_user["cum_amount"] = (
        daily_user.groupby(["population", "cost_date", "__uid__"], observed=True)["amount"]
        .cumsum()
    )
    return u, daily_user


def compute_winsor_caps(daily_user_cums, cohort_users, e, top_pct=0.01):
    if top_pct <= 0:
        caps = cohort_users[["population", "cost_date", "__uid__"]].copy()
        caps["cap_e"] = np.inf
        return caps
    du = daily_user_cums.loc[daily_user_cums["dsi"] <= (e - 1)].copy()
    if du.empty:
        caps = cohort_users[["population", "cost_date", "__uid__"]].copy()
        caps["cap_e"] = np.inf
        return caps
    per_user = (
        du.groupby(["population", "cost_date", "__uid__"], observed=True)["cum_amount"]
        .max()
        .reset_index(name="cum_e")
    )
    per_user = cohort_users.merge(per_user, on=["population", "cost_date", "__uid__"], how="left")
    per_user["cum_e"] = per_user["cum_e"].fillna(0.0)
    per_user["cap_e"] = (
        per_user.groupby(["population", "cost_date"], observed=True)["cum_e"].transform(
            lambda s: s[s > 0].quantile(1.0 - top_pct) if (s > 0).any() else np.inf
        )
    )
    return per_user[["population", "cost_date", "__uid__", "cap_e"]]


def apply_cohort_trim(daily_user_cums, cohort_users, e, trim_pct=0.10):
    du = daily_user_cums.loc[daily_user_cums["dsi"] <= (e - 1)].copy()
    if du.empty:
        return cohort_users.copy()
    per_user = (
        du.groupby(["population", "cost_date", "__uid__"], observed=True)["cum_amount"]
        .max()
        .reset_index(name="cum_e")
    )
    per_user = cohort_users.merge(per_user, on=["population", "cost_date", "__uid__"], how="left")
    per_user["cum_e"] = per_user["cum_e"].fillna(0.0)
    depositors = per_user.loc[per_user["cum_e"] > 0].copy()
    if depositors.empty:
        return cohort_users.copy()
    thresholds = (
        depositors.groupby(["population", "cost_date"], observed=True)["cum_e"]
        .quantile(1.0 - trim_pct)
        .reset_index(name="threshold")
    )
    per_user = per_user.merge(thresholds, on=["population", "cost_date"], how="left")
    per_user["threshold"] = per_user["threshold"].fillna(np.inf)
    keep = per_user.loc[
        (per_user["cum_e"] == 0) | (per_user["cum_e"] <= per_user["threshold"])
    ][["population", "cost_date", "__uid__"]]
    return keep.copy()


def get_trimmed_cohort_and_caps(population, cohort_users, daily_user_cums, e, trim_config):
    cfg = trim_config.get(population, {"method": "cohort_trim", "pct": 0.10})
    caps, trimmed = None, cohort_users
    if cfg["method"] == "winsor":
        caps = compute_winsor_caps(daily_user_cums, cohort_users, e, top_pct=cfg["pct"])
    elif cfg["method"] == "cohort_trim":
        trimmed = apply_cohort_trim(daily_user_cums, cohort_users, e, trim_pct=cfg["pct"])
    return trimmed, caps


def sum_cum_at_idx(daily_user_cums, *, cohort_users, idx, caps=None):
    du = daily_user_cums.loc[daily_user_cums["dsi"] <= idx].copy()
    if du.empty:
        out = cohort_users[["population", "cost_date"]].drop_duplicates().copy()
        out["sum_cum"] = 0.0
        return out
    per_user = (
        du.groupby(["population", "cost_date", "__uid__"], observed=True)["cum_amount"]
        .max()
        .reset_index(name="cum")
    )
    per_user = cohort_users.merge(per_user, on=["population", "cost_date", "__uid__"], how="left")
    per_user["cum"] = per_user["cum"].fillna(0.0)
    if caps is not None:
        per_user = per_user.merge(
            caps[["population", "cost_date", "__uid__", "cap_e"]],
            on=["population", "cost_date", "__uid__"],
            how="left",
        )
        per_user["cap_e"] = per_user["cap_e"].fillna(np.inf)
        per_user["cum"] = np.minimum(per_user["cum"], per_user["cap_e"])
    return (
        per_user.groupby(["population", "cost_date"], observed=True)["cum"]
        .sum()
        .reset_index(name="sum_cum")
    )


# ── experimental adaptive CV ──────────────────────────────────────────


def resolve_max_remove_fraction(s, e, policy):
    """policy keys: base (float), early_max for s in early patches, early_patches set of (s,e)."""
    base = policy.get("base", 0.15)
    early = policy.get("early_max")
    early_patches = policy.get("early_patches")  # set of (s,e) or None = all with e<=30 & s<=14
    if early is None:
        return base
    if early_patches is not None:
        return early if (s, e) in early_patches else base
    # default early = first three short windows
    if (s, e) in {(1, 7), (7, 14), (14, 30), (30, 60)}:
        return early
    return base


def rank_candidates(remaining, rank_mode):
    """Return list of cost_dates worst-first."""
    g = remaining["growth_ratio"].values
    w = remaining["sum_cum_s"].values
    dates = remaining["cost_date"].tolist()
    if rank_mode == "abs_dev":
        mu = np.nanmean(g)
        score = np.abs(g - mu)
        order = np.argsort(-score)
        return [dates[i] for i in order]
    if rank_mode == "weighted_dev":
        # distance from weighted mean, scaled by weight share
        mu, _, _ = weighted_mean_std_cv(g, w)
        wsum = np.nansum(w[np.isfinite(w) & (w > 0)])
        share = np.where(np.isfinite(w) & (w > 0) & (wsum > 0), w / wsum, 0.0)
        score = np.abs(g - mu) * share
        order = np.argsort(-score)
        return [dates[i] for i in order]
    if rank_mode == "greedy_cv_drop":
        # re-rank each step outside; here return arbitrary — caller does per-step
        return dates
    raise ValueError(rank_mode)


def best_date_by_cv_drop(remaining):
    """Pick cost_date whose removal yields lowest weighted CV on the rest."""
    best_d, best_cv = None, np.inf
    dates = remaining["cost_date"].tolist()
    if len(dates) <= 1:
        return dates[0] if dates else None
    for d in dates:
        sub = remaining.loc[remaining["cost_date"] != d]
        _, _, cv = weighted_mean_std_cv(sub["growth_ratio"].values, sub["sum_cum_s"].values)
        if np.isnan(cv):
            continue
        if cv < best_cv:
            best_cv = cv
            best_d = d
    return best_d


def patch_cv_adaptive_exp(
    u_base,
    daily_user_cums,
    *,
    population,
    s,
    e,
    as_of_date,
    trim_config,
    excluded_uids=None,
    lookback_cohorts=LOOKBACK,
    cv_threshold=0.15,
    cv_good_enough=0.10,
    remove_policy=None,
    rank_mode="abs_dev",
    stop_at="good_enough",  # good_enough | flag_line
    debug=False,
):
    remove_policy = remove_policy or {"base": 0.15}
    max_remove_fraction = resolve_max_remove_fraction(s, e, remove_policy)

    as_of_date = pd.to_datetime(as_of_date).normalize()
    cohort_end = (as_of_date - pd.Timedelta(days=e)).date()
    cohort_start = (as_of_date - pd.Timedelta(days=e + (lookback_cohorts - 1))).date()

    cohort_users = u_base.loc[
        (u_base["population"] == population)
        & (u_base["cost_date"] >= cohort_start)
        & (u_base["cost_date"] <= cohort_end)
    ][["population", "cost_date", "__uid__"]].copy()

    if cohort_users.empty:
        return pd.DataFrame(), {}, [], False, set()

    all_cohort_users = cohort_users.copy()
    n_users_in_cohort = int(cohort_users["__uid__"].nunique())
    if excluded_uids:
        cohort_users = cohort_users.loc[~cohort_users["__uid__"].isin(excluded_uids)].copy()
    n_users_after_prior = int(cohort_users["__uid__"].nunique())
    n_users_excluded_prior = n_users_in_cohort - n_users_after_prior
    if cohort_users.empty:
        return pd.DataFrame(), {}, [], False, set()

    trimmed_users, caps = get_trimmed_cohort_and_caps(
        population, cohort_users, daily_user_cums, e, trim_config
    )
    n_users_pre_trim = n_users_after_prior
    n_users_post_trim = int(trimmed_users["__uid__"].nunique())
    newly_excluded = set(cohort_users["__uid__"].unique()) - set(trimmed_users["__uid__"].unique())

    denom_w = (
        trimmed_users.groupby(["population", "cost_date"], observed=True)["__uid__"]
        .nunique()
        .reset_index(name="N_users")
    )
    sum_s = sum_cum_at_idx(
        daily_user_cums, cohort_users=trimmed_users, idx=s - 1, caps=caps
    ).rename(columns={"sum_cum": "sum_cum_s"})
    sum_e = sum_cum_at_idx(
        daily_user_cums, cohort_users=trimmed_users, idx=e - 1, caps=caps
    ).rename(columns={"sum_cum": "sum_cum_e"})
    sum_e_all = sum_cum_at_idx(
        daily_user_cums, cohort_users=all_cohort_users, idx=e - 1, caps=None
    ).rename(columns={"sum_cum": "sum_cum_e_all"})
    total_rev_before_trim = float(sum_e_all["sum_cum_e_all"].sum())

    patch = (
        denom_w.merge(sum_s, on=["population", "cost_date"]).merge(
            sum_e, on=["population", "cost_date"]
        )
    )
    patch["ARPU_s"] = patch["sum_cum_s"] / patch["N_users"]
    patch["ARPU_e"] = patch["sum_cum_e"] / patch["N_users"]
    patch["growth_ratio"] = np.where(
        patch["ARPU_s"] > 0, patch["ARPU_e"] / patch["ARPU_s"], np.nan
    )

    _, _, cv_before = weighted_mean_std_cv(patch["growth_ratio"].values, patch["sum_cum_s"].values)
    max_removable = max(1, int(np.floor(len(patch) * max_remove_fraction)))

    stop_target = cv_good_enough if stop_at == "good_enough" else cv_threshold

    removed = []
    remaining = patch.copy()

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
    total_rev_after_trim = float(patch["sum_cum_e"].sum())
    cfg = trim_config.get(population, {})

    if debug:
        tag = f"  >>> FLAG cv={cv_after:.4f}" if flagged else ""
        print(
            f"  [{population}] {s}->{e}  cv {cv_before:.4f}->{cv_after:.4f}  "
            f"rm {len(removed)}/{len(patch)} maxfrac={max_remove_fraction:.2f} "
            f"mean={mean_a:.4f}{tag}"
        )

    stats = dict(
        population=population,
        patch=f"{s}->{e}",
        cohort_start=str(cohort_start),
        cohort_end=str(cohort_end),
        n_cohort_dates_total=int(len(patch)),
        n_cohort_dates_kept=int(len(remaining)),
        n_users_excluded_prior=n_users_excluded_prior,
        n_users_pre_trim=n_users_pre_trim,
        n_users_post_trim=n_users_post_trim,
        n_users_dropped_by_trim=n_users_pre_trim - n_users_post_trim,
        total_rev_before_trim=total_rev_before_trim,
        total_rev_after_trim=total_rev_after_trim,
        cv_before=float(cv_before) if not np.isnan(cv_before) else None,
        cv_after=float(cv_after) if not np.isnan(cv_after) else None,
        mean_after=float(mean_a) if not np.isnan(mean_a) else None,
        flagged=bool(flagged),
        removed_dates=removed,
        trim_method=cfg.get("method", "none"),
        trim_pct=cfg.get("pct", 0),
        max_remove_fraction_used=max_remove_fraction,
        rank_mode=rank_mode,
    )
    return patch, stats, removed, flagged, newly_excluded


def build_curve_exp(
    u_base,
    daily_user_cums,
    *,
    population,
    as_of_date,
    trim_config,
    cv_threshold,
    cv_good_enough,
    remove_policy,
    rank_mode,
    min_cohort_dates,
    stop_at="good_enough",
    debug=False,
):
    as_of_date = pd.to_datetime(as_of_date).normalize()
    cv_rows = []
    effective = []
    excluded_uids = set()

    for s, e in PATCHES:
        patch, stats, removed, flagged, newly_excluded = patch_cv_adaptive_exp(
            u_base,
            daily_user_cums,
            population=population,
            s=s,
            e=e,
            as_of_date=as_of_date,
            trim_config=trim_config,
            excluded_uids=excluded_uids,
            cv_threshold=cv_threshold,
            cv_good_enough=cv_good_enough,
            remove_policy=remove_policy,
            rank_mode=rank_mode,
            stop_at=stop_at,
            debug=debug,
        )
        excluded_uids |= newly_excluded
        if not stats:
            continue
        if stats.get("n_cohort_dates_total", 0) < min_cohort_dates:
            continue
        cv_rows.append(stats)
        effective.append(
            {"s": s, "e": e, "removed_dates": removed, "excluded_snapshot": frozenset(excluded_uids)}
        )

    if not effective:
        return pd.DataFrame(cv_rows), pd.DataFrame()

    step_rows = []
    for ep in effective:
        s, e = ep["s"], ep["e"]
        bad_dates = set(ep["removed_dates"])
        excl = ep["excluded_snapshot"]
        start_k = 2 if s == 1 else (s + 1)
        cohort_end = (as_of_date - pd.Timedelta(days=e)).date()
        cohort_start = (as_of_date - pd.Timedelta(days=e + (LOOKBACK - 1))).date()
        cohort_users = u_base.loc[
            (u_base["population"] == population)
            & (u_base["cost_date"] >= cohort_start)
            & (u_base["cost_date"] <= cohort_end)
        ][["population", "cost_date", "__uid__"]].copy()
        if bad_dates:
            cohort_users = cohort_users.loc[~cohort_users["cost_date"].isin(bad_dates)].copy()
        if excl:
            cohort_users = cohort_users.loc[~cohort_users["__uid__"].isin(excl)].copy()
        if cohort_users.empty:
            continue
        _, caps = get_trimmed_cohort_and_caps(
            population, cohort_users, daily_user_cums, e, trim_config
        )
        denom_w = (
            cohort_users.groupby(["population", "cost_date"], observed=True)["__uid__"]
            .nunique()
            .reset_index(name="N_users")
        )
        for k in range(start_k, e + 1):
            sum_prev = sum_cum_at_idx(
                daily_user_cums, cohort_users=cohort_users, idx=k - 2, caps=caps
            ).rename(columns={"sum_cum": "sum_prev"})
            sum_curr = sum_cum_at_idx(
                daily_user_cums, cohort_users=cohort_users, idx=k - 1, caps=caps
            ).rename(columns={"sum_cum": "sum_curr"})
            tmp = (
                denom_w.merge(sum_prev, on=["population", "cost_date"]).merge(
                    sum_curr, on=["population", "cost_date"]
                )
            )
            tmp["ARPU_prev"] = tmp["sum_prev"] / tmp["N_users"]
            tmp["ARPU_curr"] = tmp["sum_curr"] / tmp["N_users"]
            tmp["step_ratio"] = np.where(
                tmp["ARPU_prev"] > 0, tmp["ARPU_curr"] / tmp["ARPU_prev"], np.nan
            )
            mean_step, _, _ = weighted_mean_std_cv(
                tmp["step_ratio"].values, tmp["sum_prev"].values
            )
            step_rows.append(
                {
                    "population": population,
                    "day": int(k),
                    "growth_step": float(mean_step),
                    "effective_patch": f"{s}->{e}",
                }
            )

    if not step_rows:
        return pd.DataFrame(cv_rows), pd.DataFrame()

    step_df = pd.DataFrame(step_rows).sort_values("day").reset_index(drop=True)
    first = effective[0]
    fs, fe = first["s"], first["e"]
    excl_first = first["excluded_snapshot"]
    base_end = (as_of_date - pd.Timedelta(days=fe)).date()
    base_start = (as_of_date - pd.Timedelta(days=fe + (LOOKBACK - 1))).date()
    base_users = u_base.loc[
        (u_base["population"] == population)
        & (u_base["cost_date"] >= base_start)
        & (u_base["cost_date"] <= base_end)
    ][["population", "cost_date", "__uid__"]].copy()
    bad_first = set(first["removed_dates"])
    if bad_first:
        base_users = base_users.loc[~base_users["cost_date"].isin(bad_first)].copy()
    if excl_first:
        base_users = base_users.loc[~base_users["__uid__"].isin(excl_first)].copy()
    _, base_caps = get_trimmed_cohort_and_caps(
        population, base_users, daily_user_cums, fe, trim_config
    )
    denom_base = (
        base_users.groupby(["population", "cost_date"], observed=True)["__uid__"]
        .nunique()
        .reset_index(name="N_users")
    )
    start_idx = 0 if fs == 1 else (fs - 1)
    sum_day1 = sum_cum_at_idx(
        daily_user_cums, cohort_users=base_users, idx=start_idx, caps=base_caps
    ).rename(columns={"sum_cum": "sum_day1"})
    base = denom_base.merge(sum_day1, on=["population", "cost_date"], how="inner")
    pooled_arpu_1 = (
        base["sum_day1"].sum() / base["N_users"].sum() if base["N_users"].sum() > 0 else 0.0
    )
    start_day = 1 if fs == 1 else fs
    out_rows = [
        {
            "population": population,
            "day": start_day,
            "ARPU_nominal": float(pooled_arpu_1),
            "growth_step": np.nan,
            "effective_patch": f"{fs}->{fe}",
        }
    ]
    arpu = float(pooled_arpu_1)
    for _, row in step_df.iterrows():
        g = row["growth_step"]
        if not np.isfinite(g):
            continue
        arpu *= float(g)
        out_rows.append(
            {
                "population": population,
                "day": int(row["day"]),
                "ARPU_nominal": float(arpu),
                "growth_step": float(g),
                "effective_patch": row["effective_patch"],
            }
        )
    curve = pd.DataFrame(out_rows).sort_values("day").reset_index(drop=True)
    all_days = pd.DataFrame({"day": range(start_day, 366)})
    curve = all_days.merge(curve, on="day", how="left")
    curve["population"] = population
    curve["effective_patch"] = curve["effective_patch"].ffill()
    curve["ARPU_nominal"] = curve["ARPU_nominal"].interpolate(method="linear", limit_area="inside")
    curve = curve.dropna(subset=["ARPU_nominal"]).reset_index(drop=True)
    curve["is_extrapolated"] = False
    return pd.DataFrame(cv_rows), curve


def extrapolate_curve_tail(curve, *, up_to_day=365, tail_days=30):
    if curve.empty:
        return curve
    last_real_day = int(curve["day"].max())
    if last_real_day >= up_to_day:
        return curve
    real = curve.loc[~curve["is_extrapolated"]].sort_values("day")
    tail = real.tail(tail_days)
    if len(tail) < 2:
        return curve
    arpu_vals = tail["ARPU_nominal"].values
    ratios = arpu_vals[1:] / arpu_vals[:-1]
    ratios = ratios[np.isfinite(ratios) & (ratios > 0)]
    if len(ratios) == 0:
        return curve
    avg_daily_growth = float(np.exp(np.mean(np.log(ratios))))
    last_arpu = float(curve.loc[curve["day"] == last_real_day, "ARPU_nominal"].iloc[0])
    last_patch = curve.loc[curve["day"] == last_real_day, "effective_patch"].iloc[0]
    new_rows = []
    arpu = last_arpu
    for d in range(last_real_day + 1, up_to_day + 1):
        arpu *= avg_daily_growth
        new_rows.append(
            {
                "population": curve["population"].iloc[0],
                "day": d,
                "ARPU_nominal": float(arpu),
                "growth_step": avg_daily_growth,
                "effective_patch": f"{last_patch} (extrapolated)",
                "is_extrapolated": True,
            }
        )
    return pd.concat([curve, pd.DataFrame(new_rows)], ignore_index=True)


# ── BQ load / cache ────────────────────────────────────────────────────


def ensure_creds():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDS)


def load_brand_tables(cfg, as_of_date=AS_OF):
    from pandas_gbq import read_gbq

    ensure_creds()
    sql_floor = (as_of_date - pd.Timedelta(days=max(GOAL_HORIZONS) + LOOKBACK + 5)).date()
    brand = cfg["brand"]
    excl_sql = ", ".join(str(a) for a in cfg["exclude_affids"])
    cost_table = cfg["cost_table"]
    dep_table = cfg["deposits_table"]
    print(f"[{brand}] BQ pull floor={sql_floor} as_of={as_of_date.date()}")

    if brand == "realprize":
        users_sql = f"""
        SELECT
          id,
          CASE
            WHEN affid IN (63, 2521, 2535, 4957, 4971, 5048, 5062, 5069) THEN 'Web'
            WHEN affid = 1 THEN 'App'
            WHEN affid IN (64, 71) THEN 'PPC'
            WHEN affid IN (0, 78, 2290) THEN 'Organic'
            ELSE 'Affiliate'
          END AS population,
          DATE(MIN(cost_date)) AS cost_date
        FROM `{cost_table}`
        WHERE cost_date >= DATE('{sql_floor}')
          AND affid NOT IN ({excl_sql})
          AND id > 0
        GROUP BY id, population
        """
    else:
        users_sql = f"""
        SELECT
          id,
          CASE
            WHEN affid IN (63, 4432, 4551, 4698, 5048, 5125, 7120, 7253, 7260, 8331, 8345) THEN 'Web'
            WHEN affid IN (64, 71) THEN 'PPC'
            WHEN affid IN (0, 78) THEN 'Organic'
            ELSE 'Affiliate'
          END AS population,
          DATE(MIN(cost_date)) AS cost_date
        FROM `{cost_table}`
        WHERE cost_date >= DATE('{sql_floor}')
          AND affid NOT IN ({excl_sql})
          AND id > 0
        GROUP BY 1, 2
        """
    revenue_sql = f"""
    SELECT
      playerId AS playerid,
      DATE(date) AS date,
      SUM(amount) / 100.0 AS amount
    FROM `{dep_table}`
    WHERE Status = 'APPROVED'
      AND date >= DATE('{sql_floor}')
    GROUP BY 1, 2
    """
    users_df = read_gbq(users_sql, project_id=PROJECT, use_bqstorage_api=True)
    revenue_df = read_gbq(revenue_sql, project_id=PROJECT, use_bqstorage_api=True)
    print(f"[{brand}] users={len(users_df):,} rev={len(revenue_df):,}")
    return users_df, revenue_df


def get_or_cache_brand(brand_key):
    CACHE.mkdir(parents=True, exist_ok=True)
    u_path = CACHE / f"{brand_key}_users.parquet"
    r_path = CACHE / f"{brand_key}_revenue.parquet"
    if u_path.exists() and r_path.exists():
        print(f"[{brand_key}] loading cache {CACHE}")
        return pd.read_parquet(u_path), pd.read_parquet(r_path)
    cfg = BRAND_CONFIGS[brand_key]
    users_df, revenue_df = load_brand_tables(cfg, AS_OF)
    users_df.to_parquet(u_path, index=False)
    revenue_df.to_parquet(r_path, index=False)
    print(f"[{brand_key}] cached -> {CACHE}")
    return users_df, revenue_df


def run_brand_cv_and_curves(brand_key, exp_cfg, debug=False):
    cfg = BRAND_CONFIGS[brand_key]
    users_df, revenue_df = get_or_cache_brand(brand_key)
    pops = list(cfg["populations"])
    trim_config = cfg["trim_config"]

    # per-pop
    u_pop, daily_pop = build_user_revenue_cums(
        users_df.loc[users_df["population"].isin(pops)].copy(), revenue_df, max_day=365
    )
    cv_parts, curve_parts = [], []
    for pop in pops:
        cv_df, curve = build_curve_exp(
            u_pop,
            daily_pop,
            population=pop,
            as_of_date=AS_OF,
            trim_config=trim_config,
            cv_threshold=cfg["cv_threshold"],
            cv_good_enough=cfg["cv_good_enough"],
            remove_policy=exp_cfg["remove_policy"],
            rank_mode=exp_cfg["rank_mode"],
            min_cohort_dates=cfg["min_cohort_dates"],
            stop_at=exp_cfg.get("stop_at", "good_enough"),
            debug=debug,
        )
        if not cv_df.empty:
            cv_parts.append(cv_df)
        if not curve.empty and cfg["extrapolate_tail"]:
            curve = extrapolate_curve_tail(
                curve, up_to_day=365, tail_days=cfg["extrapolation_tail_days"]
            )
        if not curve.empty:
            curve_parts.append(curve)

    # blended
    users_blend = users_df.copy()
    users_blend["population"] = "Blended"
    u_b, d_b = build_user_revenue_cums(users_blend, revenue_df, max_day=365)
    cv_b, curve_b = build_curve_exp(
        u_b,
        d_b,
        population="Blended",
        as_of_date=AS_OF,
        trim_config=trim_config,
        cv_threshold=cfg["cv_threshold"],
        cv_good_enough=cfg["cv_good_enough"],
        remove_policy=exp_cfg["remove_policy"],
        rank_mode=exp_cfg["rank_mode"],
        min_cohort_dates=cfg["min_cohort_dates"],
        stop_at=exp_cfg.get("stop_at", "good_enough"),
        debug=debug,
    )
    if not cv_b.empty:
        cv_parts.append(cv_b)
    if not curve_b.empty and cfg["extrapolate_tail"]:
        curve_b = extrapolate_curve_tail(
            curve_b, up_to_day=365, tail_days=cfg["extrapolation_tail_days"]
        )
    if not curve_b.empty:
        curve_parts.append(curve_b)

    cv = pd.concat(cv_parts, ignore_index=True) if cv_parts else pd.DataFrame()
    curve = pd.concat(curve_parts, ignore_index=True) if curve_parts else pd.DataFrame()
    if not cv.empty:
        cv.insert(0, "brand", brand_key)
    if not curve.empty:
        curve.insert(0, "brand", brand_key)
    return cv, curve


def raw_goal_at(curve, population, horizon, day):
    sub = curve.loc[curve["population"] == population]
    if sub.empty:
        return np.nan
    a_d = sub.loc[sub["day"] == day, "ARPU_nominal"]
    a_h = sub.loc[sub["day"] == horizon, "ARPU_nominal"]
    if a_d.empty or a_h.empty or float(a_h.iloc[0]) == 0:
        return np.nan
    return float(a_d.iloc[0] / a_h.iloc[0])


def arpu_at(curve, population, day):
    sub = curve.loc[(curve["population"] == population) & (curve["day"] == day), "ARPU_nominal"]
    return float(sub.iloc[0]) if len(sub) else np.nan


EXPERIMENTS = {
    "baseline": {
        "desc": "Production: max_remove=0.15, rank=|g−μ_unw|",
        "remove_policy": {"base": 0.15},
        "rank_mode": "abs_dev",
        "stop_at": "good_enough",
    },
    "A_early_max25": {
        "desc": "Early patches (1→7..30→60) max_remove=0.25; rest 0.15; abs_dev rank",
        "remove_policy": {
            "base": 0.15,
            "early_max": 0.25,
            "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)},
        },
        "rank_mode": "abs_dev",
        "stop_at": "good_enough",
    },
    "B_greedy_cv": {
        "desc": "max_remove=0.15; greedy leave-one-out rank (min CV after drop)",
        "remove_policy": {"base": 0.15},
        "rank_mode": "greedy_cv_drop",
        "stop_at": "good_enough",
    },
    "A+B": {
        "desc": "Early max 0.25 + greedy CV rank",
        "remove_policy": {
            "base": 0.15,
            "early_max": 0.25,
            "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)},
        },
        "rank_mode": "greedy_cv_drop",
        "stop_at": "good_enough",
    },
    "C_wdev_early25": {
        "desc": "Early max 0.25 + rank by |g−μ_w|×weight_share",
        "remove_policy": {
            "base": 0.15,
            "early_max": 0.25,
            "early_patches": {(1, 7), (7, 14), (14, 30), (30, 60)},
        },
        "rank_mode": "weighted_dev",
        "stop_at": "good_enough",
    },
}


def main():
    out_dir = ROOT / "experiments" / "cv_results_2026-08-03"
    out_dir.mkdir(parents=True, exist_ok=True)

    # warm cache first
    for b in ("realprize", "lonestar"):
        get_or_cache_brand(b)

    all_cv = {}
    all_curve = {}
    summary_rows = []

    for exp_name, exp_cfg in EXPERIMENTS.items():
        print("\n" + "=" * 70)
        print(f"EXPERIMENT: {exp_name} — {exp_cfg['desc']}")
        print("=" * 70)
        cv_list, curve_list = [], []
        for b in ("realprize", "lonestar"):
            cv, curve = run_brand_cv_and_curves(b, exp_cfg, debug=False)
            cv_list.append(cv)
            curve_list.append(curve)
        cv = pd.concat(cv_list, ignore_index=True)
        curve = pd.concat(curve_list, ignore_index=True)
        all_cv[exp_name] = cv
        all_curve[exp_name] = curve
        cv.to_csv(out_dir / f"cv_{exp_name}.csv", index=False)

        n_flag = int(cv["flagged"].sum())
        n_tot = len(cv)
        flags = cv.loc[cv["flagged"], ["brand", "population", "patch", "cv_before", "cv_after", "n_cohort_dates_kept"]]
        print(f"  flags: {n_flag}/{n_tot}")
        if not flags.empty:
            print(flags.to_string(index=False))

        # spot goals (raw ratios — organic-independent)
        for brand, pop, h, d in [
            ("realprize", "Web", 7, 1),
            ("realprize", "Web", 30, 1),
            ("realprize", "Web", 30, 7),
            ("realprize", "App", 7, 1),
            ("lonestar", "Web", 7, 1),
            ("lonestar", "Web", 30, 1),
            ("lonestar", "Blended", 7, 1),
        ]:
            subc = curve.loc[curve["brand"] == brand]
            summary_rows.append(
                {
                    "experiment": exp_name,
                    "n_flagged": n_flag,
                    "n_patches": n_tot,
                    "brand": brand,
                    "population": pop,
                    "metric": f"raw_goal_d{d}/h{h}",
                    "value": raw_goal_at(subc, pop, h, d),
                }
            )
            summary_rows.append(
                {
                    "experiment": exp_name,
                    "n_flagged": n_flag,
                    "n_patches": n_tot,
                    "brand": brand,
                    "population": pop,
                    "metric": f"ARPU_d{h}",
                    "value": arpu_at(subc, pop, h),
                }
            )

    goals_cmp = pd.DataFrame(summary_rows)
    goals_cmp.to_csv(out_dir / "spot_goals_compare.csv", index=False)

    # pivot flag table
    print("\n" + "=" * 70)
    print("FLAG COUNT BY EXPERIMENT")
    for exp_name, cv in all_cv.items():
        print(f"  {exp_name:20s}  {int(cv['flagged'].sum()):2d}/{len(cv)}")

    # detailed flag matrix for baseline vs best
    print("\nPER-PATCH cv_after (flagged cells only show ★ if flagged)")
    base = all_cv["baseline"].set_index(["brand", "population", "patch"])
    rows = []
    for exp_name, cv in all_cv.items():
        for _, r in cv.iterrows():
            rows.append(
                {
                    "experiment": exp_name,
                    "brand": r["brand"],
                    "population": r["population"],
                    "patch": r["patch"],
                    "cv_after": r["cv_after"],
                    "flagged": r["flagged"],
                    "kept": r["n_cohort_dates_kept"],
                    "mean_after": r["mean_after"],
                }
            )
    long = pd.DataFrame(rows)
    long.to_csv(out_dir / "cv_long_all_exps.csv", index=False)

    # compare mean_after on patches that were flagged in baseline
    base_flags = all_cv["baseline"].loc[all_cv["baseline"]["flagged"]]
    print("\nBaseline flagged patches — mean_after (patch growth) by experiment:")
    for _, bf in base_flags.iterrows():
        key = (bf["brand"], bf["population"], bf["patch"])
        line = f"  {key[0]}/{key[1]}/{key[2]}:"
        for exp_name, cv in all_cv.items():
            hit = cv.loc[
                (cv["brand"] == key[0])
                & (cv["population"] == key[1])
                & (cv["patch"] == key[2])
            ].iloc[0]
            star = "★" if hit["flagged"] else " "
            line += f"  {exp_name}={hit['cv_after']:.3f}{star}(mean={hit['mean_after']:.3f},k={hit['n_cohort_dates_kept']})"
        print(line)

    # delta vs baseline spot goals
    print("\nSpot goal / ARPU deltas vs baseline (%):")
    base_g = goals_cmp.loc[goals_cmp["experiment"] == "baseline"].set_index(
        ["brand", "population", "metric"]
    )["value"]
    for exp_name in EXPERIMENTS:
        if exp_name == "baseline":
            continue
        print(f"  -- {exp_name} --")
        sub = goals_cmp.loc[goals_cmp["experiment"] == exp_name]
        for _, r in sub.iterrows():
            bval = base_g.get((r["brand"], r["population"], r["metric"]), np.nan)
            if pd.isna(bval) or bval == 0 or pd.isna(r["value"]):
                continue
            # only print a subset
            if r["metric"] in (
                "raw_goal_d1/h7",
                "raw_goal_d1/h30",
                "raw_goal_d7/h30",
                "ARPU_d7",
                "ARPU_d30",
            ):
                pct = 100.0 * (r["value"] - bval) / bval
                print(
                    f"    {r['brand']}/{r['population']}/{r['metric']}: "
                    f"{bval:.4f} -> {r['value']:.4f}  ({pct:+.2f}%)"
                )

    print(f"\nWrote results under {out_dir}")


if __name__ == "__main__":
    main()
