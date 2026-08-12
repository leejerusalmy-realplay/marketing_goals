#!/usr/bin/env python3
"""Build cv_diagnosis Colab from generic Combined. Does NOT touch robust_cv."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERIC = ROOT / "notebooks" / "Marketing_Goals_Combined_RP_LS_Colab.ipynb"
OUT_DIR = Path(__file__).resolve().parent
OUT_NB = OUT_DIR / "Marketing_Goals_Combined_RP_LS_Colab.ipynb"


def get_src(nb, i):
    return "".join(nb["cells"][i].get("source", []))


def set_src(nb, i, new_src: str):
    if not new_src.endswith("\n"):
        new_src += "\n"
    nb["cells"][i]["source"] = new_src.splitlines(keepends=True)
    if nb["cells"][i]["cell_type"] == "code":
        nb["cells"][i]["outputs"] = []
        nb["cells"][i]["execution_count"] = None


def make_code_cell(src: str) -> dict:
    if not src.endswith("\n"):
        src += "\n"
    return {
        "cell_type": "code",
        "metadata": {},
        "source": src.splitlines(keepends=True),
        "outputs": [],
        "execution_count": None,
    }


def make_md_cell(src: str) -> dict:
    if not src.endswith("\n"):
        src += "\n"
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": src.splitlines(keepends=True),
    }


NEW_PATCH_CV = r'''# ══════════════════════════════════════════════════════════════
# ADAPTIVE CV ANALYSIS — persistent trim
# + DIAGNOSIS instrumentation (same CV math; extra tables only)
# ══════════════════════════════════════════════════════════════

# Accumulated during diagnosis run (reset in the RUN cell)
CV_DIAG_DATE_ROWS = []
CV_DIAG_DIST_ROWS = []


def _dist_stats(values, prefix):
    """Distribution stats on cohort-level growth_ratio observations."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    out = {
        f'n_observations_{prefix}': int(x.size),
        f'mean_{prefix}': None,
        f'std_{prefix}': None,
        f'min_{prefix}': None,
        f'p10_{prefix}': None,
        f'p25_{prefix}': None,
        f'median_{prefix}': None,
        f'p75_{prefix}': None,
        f'p90_{prefix}': None,
        f'p95_{prefix}': None,
        f'max_{prefix}': None,
        f'iqr_{prefix}': None,
        f'pct_zero_{prefix}': None,
        f'pct_near_zero_{prefix}': None,
        f'skewness_{prefix}': None,
    }
    if x.size == 0:
        return out
    s = pd.Series(x)
    q10, q25, q50, q75, q90, q95 = np.percentile(x, [10, 25, 50, 75, 90, 95])
    out.update({
        f'mean_{prefix}': float(np.mean(x)),
        f'std_{prefix}': float(np.std(x, ddof=0)),
        f'min_{prefix}': float(np.min(x)),
        f'p10_{prefix}': float(q10),
        f'p25_{prefix}': float(q25),
        f'median_{prefix}': float(q50),
        f'p75_{prefix}': float(q75),
        f'p90_{prefix}': float(q90),
        f'p95_{prefix}': float(q95),
        f'max_{prefix}': float(np.max(x)),
        f'iqr_{prefix}': float(q75 - q25),
        f'pct_zero_{prefix}': float(np.mean(x == 0.0)),
        f'pct_near_zero_{prefix}': float(np.mean(np.abs(x) <= NEAR_ZERO_GROWTH)),
        f'skewness_{prefix}': float(s.skew()) if x.size >= 3 else None,
    })
    return out


def _user_level_rev_at_e(daily_user_cums, cohort_users, e, caps=None):
    """Per-user cumulative revenue at patch end (idx = e-1), after optional winsor caps."""
    idx = e - 1
    grp_cols = ['population', 'cost_date']
    if idx < 0 or cohort_users.empty:
        return pd.DataFrame(columns=grp_cols + ['__uid__', 'cum'])
    du = daily_user_cums.loc[daily_user_cums['dsi'] <= idx].copy()
    if du.empty:
        per_user = cohort_users[grp_cols + ['__uid__']].copy()
        per_user['cum'] = 0.0
        return per_user
    per_user = (
        du.groupby(grp_cols + ['__uid__'], observed=True)['cum_amount']
          .max().reset_index(name='cum')
    )
    per_user = cohort_users.merge(per_user, on=grp_cols + ['__uid__'], how='left')
    per_user['cum'] = per_user['cum'].fillna(0.0)
    if caps is not None:
        per_user = per_user.merge(caps, on=grp_cols + ['__uid__'], how='left')
        per_user['cap_e'] = per_user['cap_e'].fillna(np.inf)
        per_user['cum'] = np.minimum(per_user['cum'], per_user['cap_e'])
    return per_user[grp_cols + ['__uid__', 'cum']]


def _cohort_date_user_stats(per_user):
    """Whale / payer diagnostics per cost_date from user-level cum at e."""
    rows = []
    if per_user.empty:
        return pd.DataFrame()
    for (pop, cd), g in per_user.groupby(['population', 'cost_date'], observed=True):
        cum = g['cum'].to_numpy(dtype=float)
        n = int(cum.size)
        total = float(cum.sum())
        payers = int(np.sum(cum > 0))
        order = np.sort(cum)[::-1]
        top1 = float(order[0]) if n else 0.0
        top5 = float(order[:5].sum()) if n else 0.0
        rows.append({
            'population': pop,
            'cost_date': cd,
            'n_users': n,
            'total_revenue': total,
            'n_payers': payers,
            'payer_rate': (payers / n) if n else None,
            'ARPPU': (total / payers) if payers else None,
            'max_user_revenue': top1,
            'top1_user_revenue_share': (top1 / total) if total > 0 else None,
            'top5_users_revenue_share': (top5 / total) if total > 0 else None,
            'pct_users_zero_revenue': float(np.mean(cum == 0.0)) if n else None,
            'pct_users_near_zero_revenue': float(np.mean(np.abs(cum) <= NEAR_ZERO_USER_REV)) if n else None,
        })
    return pd.DataFrame(rows)


def patch_cv_adaptive(
    u_base, daily_user_cums, *,
    population, s, e, as_of_date,
    excluded_uids=None,
    lookback_cohorts=None,
    cv_threshold=None,
    cv_good_enough=None,
    max_remove_fraction=None,
    debug=True,
):
    # Resolve defaults at call time (after brand config applied)
    if lookback_cohorts is None:
        lookback_cohorts = LOOKBACK_COHORTS
    if cv_threshold is None:
        cv_threshold = CV_THRESHOLD
    if cv_good_enough is None:
        cv_good_enough = CV_GOOD_ENOUGH
    if max_remove_fraction is None:
        max_remove_fraction = MAX_REMOVE_FRACTION
    as_of_date = pd.to_datetime(as_of_date).normalize()
    cohort_end = (as_of_date - pd.Timedelta(days=e)).date()
    cohort_start = (as_of_date - pd.Timedelta(days=e + (lookback_cohorts - 1))).date()
    brand = globals().get('ACTIVE_BRAND', None)

    cohort_users = u_base.loc[
        (u_base['population'] == population) &
        (u_base['cost_date'] >= cohort_start) &
        (u_base['cost_date'] <= cohort_end)
    ][['population', 'cost_date', '__uid__']].copy()

    if cohort_users.empty:
        return pd.DataFrame(), {}, [], False, set()

    all_cohort_users = cohort_users.copy()
    n_users_in_cohort = int(cohort_users['__uid__'].nunique())

    if excluded_uids:
        cohort_users = cohort_users.loc[
            ~cohort_users['__uid__'].isin(excluded_uids)
        ].copy()

    n_users_after_prior = int(cohort_users['__uid__'].nunique())
    n_users_excluded_prior = n_users_in_cohort - n_users_after_prior

    if cohort_users.empty:
        return pd.DataFrame(), {}, [], False, set()

    trimmed_users, caps = get_trimmed_cohort_and_caps(
        population, cohort_users, daily_user_cums, e
    )
    n_users_pre_trim = n_users_after_prior
    n_users_post_trim = int(trimmed_users['__uid__'].nunique())

    newly_excluded = (
        set(cohort_users['__uid__'].unique()) - set(trimmed_users['__uid__'].unique())
    )

    denom_w = (
        trimmed_users.groupby(['population', 'cost_date'], observed=True)['__uid__']
                     .nunique().reset_index(name='N_users')
    )
    sum_s = sum_cum_at_idx(
        daily_user_cums, cohort_users=trimmed_users, idx=s - 1, caps=caps
    ).rename(columns={'sum_cum': 'sum_cum_s'})
    sum_e = sum_cum_at_idx(
        daily_user_cums, cohort_users=trimmed_users, idx=e - 1, caps=caps
    ).rename(columns={'sum_cum': 'sum_cum_e'})

    sum_e_all = sum_cum_at_idx(
        daily_user_cums, cohort_users=all_cohort_users, idx=e - 1, caps=None
    ).rename(columns={'sum_cum': 'sum_cum_e_all'})
    total_rev_before_trim = float(sum_e_all['sum_cum_e_all'].sum())

    patch = (
        denom_w
        .merge(sum_s, on=['population', 'cost_date'])
        .merge(sum_e, on=['population', 'cost_date'])
    )
    patch['ARPU_s'] = patch['sum_cum_s'] / patch['N_users']
    patch['ARPU_e'] = patch['sum_cum_e'] / patch['N_users']
    patch['growth_ratio'] = np.where(
        patch['ARPU_s'] > 0, patch['ARPU_e'] / patch['ARPU_s'], np.nan
    )

    # ── EXISTING CV (unchanged) ──
    _, _, cv_before = weighted_mean_std_cv(patch['growth_ratio'].values, patch['sum_cum_s'].values)

    mu_unw = np.nanmean(patch['growth_ratio'].values)
    patch['abs_dev'] = (patch['growth_ratio'] - mu_unw).abs()
    sorted_dates = patch.sort_values('abs_dev', ascending=False)['cost_date'].tolist()
    max_removable = max(1, int(np.floor(len(patch) * max_remove_fraction)))

    removed = []
    remaining = patch.copy()

    for candidate in sorted_dates:
        _, _, cv_now = weighted_mean_std_cv(
            remaining['growth_ratio'].values, remaining['sum_cum_s'].values
        )
        if np.isnan(cv_now) or cv_now <= cv_good_enough:
            break
        if len(removed) >= max_removable:
            break
        removed.append(candidate)
        remaining = remaining.loc[~remaining['cost_date'].isin(removed)]

    mean_a, _, cv_after = weighted_mean_std_cv(
        remaining['growth_ratio'].values, remaining['sum_cum_s'].values
    )
    flagged = (not np.isnan(cv_after)) and (cv_after > cv_threshold)
    total_rev_after_trim = float(patch['sum_cum_e'].sum())
    cfg = TRIM_CONFIG.get(population, {})

    # ── DIAGNOSIS ONLY (does not affect CV / flagged) ──
    dist_before = _dist_stats(patch['growth_ratio'].values, 'before')
    dist_after = _dist_stats(remaining['growth_ratio'].values, 'after')

    per_user = _user_level_rev_at_e(daily_user_cums, trimmed_users, e, caps=caps)
    user_zero_pct = float((per_user['cum'] == 0).mean()) if len(per_user) else None
    user_near_zero_pct = float((per_user['cum'].abs() <= NEAR_ZERO_USER_REV).mean()) if len(per_user) else None
    date_user = _cohort_date_user_stats(per_user)

    med_unw = np.nanmedian(patch['growth_ratio'].values)
    patch_detail = patch.copy()
    patch_detail['distance_from_mean'] = patch_detail['growth_ratio'] - mu_unw
    patch_detail['distance_from_median'] = patch_detail['growth_ratio'] - med_unw
    finite = patch_detail['growth_ratio'].notna()
    patch_detail['percentile_rank'] = np.nan
    if finite.any():
        patch_detail.loc[finite, 'percentile_rank'] = (
            patch_detail.loc[finite, 'growth_ratio'].rank(pct=True)
        )
    removed_set = set(removed)
    patch_detail['was_removed_by_existing_trim'] = patch_detail['cost_date'].isin(removed_set)
    # note: column name kept as requested; means removed by CV date-cleanup (not winsor)

    if not date_user.empty:
        patch_detail = patch_detail.merge(date_user, on=['population', 'cost_date'], how='left')

    # time trend on BEFORE observations (full window used for cv_before)
    trend_corr = None
    trend_slope = None
    trend_strength = None
    tdf = patch_detail.dropna(subset=['growth_ratio', 'cost_date']).copy()
    if len(tdf) >= 3:
        tord = pd.to_datetime(tdf['cost_date']).map(pd.Timestamp.toordinal).astype(float)
        y = tdf['growth_ratio'].astype(float)
        if tord.nunique() >= 2 and np.nanstd(y) > 0:
            trend_corr = float(np.corrcoef(tord, y)[0, 1])
            slope, intercept = np.polyfit(tord, y, 1)
            trend_slope = float(slope)
            # strength: |corr|; "strong" if |corr| >= TREND_CORR_STRONG
            trend_strength = abs(trend_corr)

    if debug:
        flag_tag = f'  >>> FLAGGED (cv={cv_after:.4f} > {cv_threshold})' if flagged else ''
        print(
            f'  [{population}] {s}->{e}  '
            f'cv {cv_before:.4f}->{cv_after:.4f}  '
            f'removed={len(removed)}/{len(patch)}  '
            f'excl_prior={n_users_excluded_prior:,}  '
            f'pre/post={n_users_pre_trim:,}/{n_users_post_trim:,}  '
            f'newly_excl={len(newly_excluded):,}{flag_tag}'
        )

    stats = dict(
        population=population,
        patch=f'{s}->{e}',
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
        trim_method=cfg.get('method', 'none'),
        trim_pct=cfg.get('pct', 0),
        # diagnosis extras
        pct_users_zero_revenue=user_zero_pct,
        pct_users_near_zero_revenue=user_near_zero_pct,
        pct_cohort_metric_zero_before=dist_before['pct_zero_before'],
        pct_cohort_metric_near_zero_before=dist_before['pct_near_zero_before'],
        pct_cohort_metric_zero_after=dist_after['pct_zero_after'],
        pct_cohort_metric_near_zero_after=dist_after['pct_near_zero_after'],
        time_trend_corr=trend_corr,
        time_trend_slope_per_day=trend_slope,
        time_trend_strength=trend_strength,
        time_trend_flag=bool(trend_strength is not None and trend_strength >= TREND_CORR_STRONG),
        cv_threshold_used=float(cv_threshold),
        near_zero_growth_threshold=float(NEAR_ZERO_GROWTH),
        near_zero_user_rev_threshold=float(NEAR_ZERO_USER_REV),
    )
    stats.update(dist_before)
    stats.update(dist_after)

    # accumulate detail rows
    detail = patch_detail.copy()
    detail.insert(0, 'brand', brand)
    detail.insert(2, 'patch', f'{s}->{e}')
    detail = detail.rename(columns={
        'cost_date': 'cohort_date',
        'growth_ratio': 'cohort_metric_used_for_cv',
        'N_users': 'n_users_from_patch',
    })
    # prefer user-stats n_users when present
    if 'n_users' not in detail.columns and 'n_users_from_patch' in detail.columns:
        detail['n_users'] = detail['n_users_from_patch']
    elif 'n_users' in detail.columns:
        detail['n_users'] = detail['n_users'].fillna(detail.get('n_users_from_patch'))
    CV_DIAG_DATE_ROWS.append(detail)
    CV_DIAG_DIST_ROWS.append({**{'brand': brand}, **stats})

    return patch, stats, removed, flagged, newly_excluded


print('Adaptive CV function defined (persistent trim + diagnosis instrumentation).')
'''

DIAG_RUN = r'''# ══════════════════════════════════════════════════════════════
# DIAGNOSIS RUN — CV observations only (no organic / goals)
# Uses the same Part 1+2 path as Marketing Goals (per-pop + Blended).
# ══════════════════════════════════════════════════════════════

CV_DIAG_DATE_ROWS.clear()
CV_DIAG_DIST_ROWS.clear()

brand_results = {}
cv_all = []

for brand_key in RUN_BRANDS:
    cfg = BRAND_CONFIGS[brand_key]
    apply_brand_globals(cfg)
    brand = cfg['brand']
    users_df, revenue_df = load_brand_tables(cfg, as_of_date=AS_OF_DATE)
    print(f'\n[{brand}] loaded users={len(users_df):,} revenue_rows={len(revenue_df):,}')

    # PART 1 — per-population (same as production pipeline)
    u_pop, daily_pop = build_user_revenue_cums(
        users_df.loc[users_df['population'].isin(POPULATIONS)].copy(),
        revenue_df,
        max_day=365,
    )
    cv_pop_df, _curve_pop = build_all_populations(
        u_pop, daily_pop,
        as_of_date=AS_OF_DATE,
        extrapolate_tail=False,  # diagnosis does not need curve tail
        debug=True,
    )

    # PART 2 — Blended (same as production)
    users_blend = users_df.copy()
    users_blend['population'] = 'Blended'
    u_blend, daily_blend = build_user_revenue_cums(users_blend, revenue_df, max_day=365)
    _BLENDED_POPS_BACKUP = list(POPULATIONS)
    POPULATIONS = ['Blended']
    try:
        cv_blend_df, _curve_blend = build_all_populations(
            u_blend, daily_blend,
            as_of_date=AS_OF_DATE,
            extrapolate_tail=False,
            debug=True,
        )
    finally:
        POPULATIONS = _BLENDED_POPS_BACKUP

    cv_brand = pd.concat(
        [x for x in [cv_pop_df, cv_blend_df] if x is not None and not x.empty],
        ignore_index=True,
    )
    if not cv_brand.empty:
        cv_brand.insert(0, 'brand', brand)
        cv_all.append(cv_brand)
    brand_results[brand_key] = {'cv': cv_brand, 'users': users_df}

cv_df = pd.concat(cv_all, ignore_index=True) if cv_all else pd.DataFrame()
dist_df = pd.DataFrame(CV_DIAG_DIST_ROWS)
date_df = pd.concat(CV_DIAG_DATE_ROWS, ignore_index=True) if CV_DIAG_DATE_ROWS else pd.DataFrame()

print('\n' + '=' * 60)
print('CV DIAGNOSIS RUN COMPLETE')
print(f'  as_of_date     = {AS_OF_DATE.date()}')
print(f'  experiment     = {EXPERIMENT_TAG}')
print(f'  cv summary rows= {len(cv_df):,}')
print(f'  dist rows      = {len(dist_df):,}')
print(f'  date detail    = {len(date_df):,}')
print(f'  NEAR_ZERO_GROWTH   = {NEAR_ZERO_GROWTH}')
print(f'  NEAR_ZERO_USER_REV = {NEAR_ZERO_USER_REV}')
print(f'  TREND_CORR_STRONG  = {TREND_CORR_STRONG}')
print('=' * 60)
'''

DIAG_ANALYSIS = r'''# ══════════════════════════════════════════════════════════════
# DIAGNOSIS ANALYSIS — distributions, zeros, dates, sample size,
# patch maturity, trends, plots, final notes
# ══════════════════════════════════════════════════════════════

import matplotlib.pyplot as plt

assert not dist_df.empty, 'dist_df empty — run the diagnosis RUN cell first'

# Merge official cv flagged onto dist (should already be in dist_df)
summary = dist_df.copy()
if 'flagged' not in summary.columns and not cv_df.empty:
    summary = summary.merge(
        cv_df[['brand', 'population', 'patch', 'flagged', 'cv_before', 'cv_after']],
        on=['brand', 'population', 'patch'],
        how='left',
        suffixes=('', '_cv'),
    )

summary['cv_reduction_from_trim'] = summary.apply(
    lambda r: (None if r.get('cv_before') is None or r.get('cv_after') is None
               else float(r['cv_before']) - float(r['cv_after'])),
    axis=1,
)

high = summary.loc[summary['flagged'] == True].copy()
print(f'High-CV / flagged patches (existing model rule): {len(high)} / {len(summary)}')

# Focus cases helper
FOCUS_SET = {(b, p, patch) for b, p, patch in FOCUS_CASES}
summary['is_focus_case'] = summary.apply(
    lambda r: (r['brand'], r['population'], r['patch']) in FOCUS_SET, axis=1
)

# ── Distribution table (before / after) ──
dist_cols = [
    'brand', 'population', 'patch',
    'n_observations_before', 'mean_before', 'std_before', 'cv_before',
    'min_before', 'p10_before', 'p25_before', 'median_before', 'p75_before',
    'p90_before', 'p95_before', 'max_before', 'iqr_before',
    'pct_zero_before', 'pct_near_zero_before', 'skewness_before',
    'n_observations_after', 'mean_after', 'std_after', 'cv_after',
    'min_after', 'p10_after', 'p25_after', 'median_after', 'p75_after',
    'p90_after', 'p95_after', 'max_after', 'iqr_after',
    'pct_zero_after', 'pct_near_zero_after', 'skewness_after',
    'flagged', 'is_focus_case',
]
dist_cols = [c for c in dist_cols if c in summary.columns]
print('\n=== Distribution diagnostics (all patches) ===')
print(summary[dist_cols].sort_values(['brand', 'population', 'patch']).to_string(index=False))

# ── Zero inflation: user-level vs cohort-level ──
zero_cols = [
    'brand', 'population', 'patch', 'flagged',
    'pct_users_zero_revenue', 'pct_users_near_zero_revenue',
    'pct_cohort_metric_zero_before', 'pct_cohort_metric_near_zero_before',
    'pct_cohort_metric_zero_after', 'pct_cohort_metric_near_zero_after',
    'n_users_post_trim', 'n_cohort_dates_total',
]
zero_cols = [c for c in zero_cols if c in summary.columns]
print('\n=== Zero / near-zero: user-level cum@e vs cohort growth_ratio ===')
print(f'(NEAR_ZERO_USER_REV={NEAR_ZERO_USER_REV}, NEAR_ZERO_GROWTH={NEAR_ZERO_GROWTH})')
print(summary[zero_cols].sort_values(['flagged', 'brand'], ascending=[False, True]).to_string(index=False))

# ── Per-date detail for flagged + focus ──
interesting_keys = set(zip(high['brand'], high['population'], high['patch'])) | FOCUS_SET
if not date_df.empty:
    date_focus = date_df.loc[
        date_df.apply(lambda r: (r['brand'], r['population'], r['patch']) in interesting_keys, axis=1)
    ].copy()
else:
    date_focus = pd.DataFrame()

print('\n=== Per cohort-date detail (flagged + focus cases) ===')
show_date_cols = [c for c in [
    'brand', 'population', 'patch', 'cohort_date', 'n_users',
    'cohort_metric_used_for_cv', 'distance_from_mean', 'distance_from_median',
    'percentile_rank', 'was_removed_by_existing_trim',
    'total_revenue', 'n_payers', 'payer_rate', 'ARPPU',
    'max_user_revenue', 'top1_user_revenue_share', 'top5_users_revenue_share',
    'pct_users_zero_revenue',
] if c in date_focus.columns]
if date_focus.empty:
    print('(no date detail)')
else:
    print(date_focus[show_date_cols].sort_values(
        ['brand', 'population', 'patch', 'cohort_date']
    ).to_string(index=False))

# Easy inspection blocks for known focus cases
print('\n=== Focus-case inspection blocks ===')
for brand, pop, patch in FOCUS_CASES:
    sub_s = summary.loc[
        (summary['brand'] == brand) & (summary['population'] == pop) & (summary['patch'] == patch)
    ]
    sub_d = date_df.loc[
        (date_df['brand'] == brand) & (date_df['population'] == pop) & (date_df['patch'] == patch)
    ] if not date_df.empty else pd.DataFrame()
    print(f'\n── {brand} | {pop} | {patch} ──')
    if sub_s.empty:
        print('  (not in this run)')
        continue
    r = sub_s.iloc[0]
    print(
        f"  cv {r.get('cv_before')} → {r.get('cv_after')}  flagged={r.get('flagged')}  "
        f"n_users={r.get('n_users_post_trim')}  n_dates={r.get('n_cohort_dates_total')}  "
        f"trend_corr={r.get('time_trend_corr')}  skew_after={r.get('skewness_after')}"
    )
    if not sub_d.empty:
        top = sub_d.assign(_abs=sub_d['distance_from_mean'].abs()).nlargest(5, '_abs')
        cols = [c for c in ['cohort_date', 'cohort_metric_used_for_cv', 'distance_from_mean',
                            'was_removed_by_existing_trim', 'top1_user_revenue_share', 'n_users']
                if c in top.columns]
        print(top[cols].to_string(index=False))

# ── Sample size exploration ──
print('\n=== Sample size vs CV after (exploratory) ===')
ss = summary.dropna(subset=['cv_after']).copy()
if not ss.empty:
    print('Correlation CV_after vs n_users_post_trim:',
          float(ss['cv_after'].corr(ss['n_users_post_trim'])) if ss['n_users_post_trim'].std() else None)
    print('Correlation CV_after vs n_cohort_dates_total:',
          float(ss['cv_after'].corr(ss['n_cohort_dates_total'])) if ss['n_cohort_dates_total'].std() else None)
    ss['user_bucket'] = pd.cut(
        ss['n_users_post_trim'],
        bins=[-np.inf, 500, 2000, 10000, np.inf],
        labels=['<=500', '501-2000', '2001-10000', '>10000'],
    )
    print(ss.groupby('user_bucket', observed=True).agg(
        n=('cv_after', 'count'),
        median_cv_after=('cv_after', 'median'),
        mean_cv_after=('cv_after', 'mean'),
        pct_flagged=('flagged', 'mean'),
    ).to_string())
    print('\nRealPrize Web only:')
    rpweb = ss.loc[(ss['brand'] == 'realprize') & (ss['population'] == 'Web')]
    if rpweb.empty:
        print('(none)')
    else:
        print(rpweb[['patch', 'cv_after', 'n_users_post_trim', 'n_cohort_dates_total', 'flagged']]
              .sort_values('cv_after', ascending=False).to_string(index=False))

# ── Patch maturity ──
print('\n=== Patch maturity — CV distribution by patch ===')
patch_order = [f'{a}->{b}' for a, b in PATCHES]

def patch_maturity_table(df, label):
    print(f'\n-- {label} --')
    if df.empty:
        print('(empty)')
        return
    g = df.groupby('patch', sort=False)
    rows = []
    for patch in patch_order:
        if patch not in g.groups:
            continue
        sub = g.get_group(patch)
        rows.append({
            'patch': patch,
            'median_cv_before': sub['cv_before'].median(),
            'median_cv_after': sub['cv_after'].median(),
            'mean_cv_after': sub['cv_after'].mean(),
            'p75_cv_after': sub['cv_after'].quantile(0.75),
            'p90_cv_after': sub['cv_after'].quantile(0.90),
            'max_cv_after': sub['cv_after'].max(),
            'n_populations': len(sub),
            'n_flagged': int(sub['flagged'].sum()),
            'pct_flagged': float(sub['flagged'].mean()),
        })
    print(pd.DataFrame(rows).to_string(index=False))

patch_maturity_table(summary, 'Overall')
for brand in summary['brand'].dropna().unique():
    patch_maturity_table(summary.loc[summary['brand'] == brand], f'Brand={brand}')

# ── Time trends among high CV ──
print('\n=== Time-trend flags among high-CV patches ===')
trend_cols = [c for c in [
    'brand', 'population', 'patch', 'cv_after', 'time_trend_corr',
    'time_trend_slope_per_day', 'time_trend_strength', 'time_trend_flag', 'flagged',
] if c in summary.columns]
print(summary.loc[summary['flagged'] == True, trend_cols]
      .sort_values('time_trend_strength', ascending=False).to_string(index=False))

# ── Plots ──
def _plot_case(brand, pop, patch):
    sub = date_df.loc[
        (date_df['brand'] == brand) & (date_df['population'] == pop) & (date_df['patch'] == patch)
    ].sort_values('cohort_date')
    if sub.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    vals = sub['cohort_metric_used_for_cv'].astype(float)
    axes[0].hist(vals.dropna(), bins=min(15, max(5, vals.notna().sum())), color='steelblue', edgecolor='white')
    removed = sub['was_removed_by_existing_trim'] == True
    axes[0].set_title(f'{brand} {pop} {patch}\ngrowth_ratio distribution')
    axes[0].set_xlabel('cohort_metric_used_for_cv (growth_ratio)')
    axes[1].scatter(pd.to_datetime(sub.loc[~removed, 'cohort_date']),
                    sub.loc[~removed, 'cohort_metric_used_for_cv'], label='kept', s=40)
    if removed.any():
        axes[1].scatter(pd.to_datetime(sub.loc[removed, 'cohort_date']),
                        sub.loc[removed, 'cohort_metric_used_for_cv'],
                        label='removed by CV cleanup', c='red', s=50, marker='x')
    axes[1].set_title('cohort_date → growth_ratio')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].legend(fontsize=8)
    plt.tight_layout()
    plt.show()

print('\n=== Visuals: flagged / focus cases ===')
plot_keys = sorted(interesting_keys)
for brand, pop, patch in plot_keys:
    _plot_case(brand, pop, patch)

# CV vs sample size
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(summary['n_users_post_trim'], summary['cv_after'],
           c=summary['flagged'].map({True: 'red', False: 'steelblue'}), alpha=0.75)
ax.set_xlabel('n_users_post_trim')
ax.set_ylabel('cv_after')
ax.set_title('CV after vs user count (red = flagged)')
plt.tight_layout()
plt.show()

# CV by patch boxplot
fig, ax = plt.subplots(figsize=(10, 5))
order = [p for p in patch_order if p in set(summary['patch'])]
data = [summary.loc[summary['patch'] == p, 'cv_after'].dropna().values for p in order]
ax.boxplot(data, labels=order, vert=True)
ax.axhline(0.15, color='grey', ls='--', lw=1, label='0.15 reference')
ax.set_title('CV after by patch (all brand×population)')
ax.tick_params(axis='x', rotation=45)
ax.legend()
plt.tight_layout()
plt.show()

# Before vs after CV
fig, ax = plt.subplots(figsize=(6, 6))
ax.scatter(summary['cv_before'], summary['cv_after'], alpha=0.75)
lim = max(summary['cv_before'].max(), summary['cv_after'].max()) * 1.05
ax.plot([0, lim], [0, lim], '--', color='grey')
ax.set_xlabel('cv_before')
ax.set_ylabel('cv_after')
ax.set_title('Existing date-cleanup: CV before vs after')
plt.tight_layout()
plt.show()

# ── Final diagnostic notes table ──
def _notes(r):
    notes = []
    cv_a = r.get('cv_after')
    cv_b = r.get('cv_before')
    if cv_a is not None and cv_b is not None and cv_a > 0.15 and (cv_b - cv_a) < 0.02:
        notes.append('CV remains high even after extreme dates are removed')
    # concentration: share of abs_dev in top 2 dates
    key = (r['brand'], r['population'], r['patch'])
    dsub = date_df.loc[
        (date_df['brand'] == key[0]) & (date_df['population'] == key[1]) & (date_df['patch'] == key[2])
    ] if not date_df.empty else pd.DataFrame()
    if not dsub.empty and dsub['distance_from_mean'].notna().any():
        absdev = dsub['distance_from_mean'].abs().fillna(0)
        tot = absdev.sum()
        if tot > 0 and absdev.nlargest(2).sum() / tot >= 0.40:
            notes.append('High CV appears concentrated in a few extreme cohort dates')
        elif r.get('iqr_after') is not None and r.get('median_after') not in (None, 0):
            if r['iqr_after'] / abs(r['median_after']) >= 0.25:
                notes.append('Broad dispersion across most cohort dates')
    if r.get('n_users_post_trim') is not None and r['n_users_post_trim'] < 2000:
        notes.append('Small sample size may contribute to instability')
    if r.get('time_trend_flag'):
        direction = 'upward' if (r.get('time_trend_corr') or 0) > 0 else 'downward'
        notes.append(f'Strong {direction} cohort-date trend')
    if r.get('skewness_after') is not None and abs(r['skewness_after']) >= 1.0:
        notes.append('Large mean-median difference / strong right skew' if r['skewness_after'] > 0
                     else 'Strong left skew / mean-median gap')
    if (r.get('pct_users_zero_revenue') or 0) >= 0.5 and (r.get('pct_cohort_metric_zero_before') or 0) < 0.05:
        notes.append('User-level zeros common, but cohort growth_ratio rarely zero (aggregation)')
    if (r.get('pct_cohort_metric_near_zero_before') or 0) >= 0.1:
        notes.append('Material share of near-zero cohort growth ratios')
    # whale share on max growth date
    if not dsub.empty and 'top1_user_revenue_share' in dsub.columns:
        top_share = dsub.loc[dsub['cohort_metric_used_for_cv'].idxmax(), 'top1_user_revenue_share'] if dsub['cohort_metric_used_for_cv'].notna().any() else None
        if top_share is not None and top_share >= 0.25:
            notes.append('High cohort metric may be whale-driven (top1 user revenue share high on peak date)')
    if not notes:
        notes.append('No obvious single driver — requires further investigation')
    return ' | '.join(notes)

final_cols_src = [
    'brand', 'population', 'patch', 'cv_before', 'cv_after',
    'n_users_post_trim', 'n_cohort_dates_total',
    'mean_after', 'median_after', 'p10_after', 'p90_after', 'max_after',
    'pct_zero_after', 'skewness_after', 'cv_reduction_from_trim', 'time_trend_strength',
]
final = high.copy() if not high.empty else summary.loc[summary['is_focus_case']].copy()
for c in final_cols_src:
    if c not in final.columns:
        final[c] = None
final = final.rename(columns={
    'n_users_post_trim': 'n_users',
    'n_cohort_dates_total': 'n_cohort_dates',
    'mean_after': 'mean',
    'median_after': 'median',
    'p10_after': 'p10',
    'p90_after': 'p90',
    'max_after': 'max',
    'pct_zero_after': 'pct_zero',
    'skewness_after': 'skewness',
})
final['diagnostic_notes'] = high.apply(_notes, axis=1) if not high.empty else final.apply(_notes, axis=1)
# rebuild notes on final rows properly
final['diagnostic_notes'] = final.apply(
    lambda r: _notes(summary.loc[
        (summary['brand'] == r['brand']) & (summary['population'] == r['population']) & (summary['patch'] == r['patch'])
    ].iloc[0]) if not summary.loc[
        (summary['brand'] == r['brand']) & (summary['population'] == r['population']) & (summary['patch'] == r['patch'])
    ].empty else 'n/a',
    axis=1,
)

final_view_cols = [
    'brand', 'population', 'patch', 'cv_before', 'cv_after',
    'n_users', 'n_cohort_dates', 'mean', 'median', 'p10', 'p90', 'max',
    'pct_zero', 'skewness', 'cv_reduction_from_trim', 'time_trend_strength',
    'diagnostic_notes',
]
print('\n=== FINAL diagnostic table (high-CV / flagged) ===')
print(final[final_view_cols].sort_values('cv_after', ascending=False).to_string(index=False))

print('\n=== Brief read (diagnosis only — no methodology change) ===')
print(
    'Inspect flagged rows and focus cases above. High CV can come from a few extreme '
    'cohort dates, broad dispersion, small N, temporal trends, skew/whales, or zeros — '
    'check user-level vs cohort-level zero tables before attributing CV to zero inflation. '
    'This notebook does not change Marketing Goals CV, thresholds, or trimming.'
)
'''

DIAG_EXPORT = r'''# ══════════════════════════════════════════════════════════════
# EXPORT — diagnosis CSVs only (does not overwrite other experiments)
# ══════════════════════════════════════════════════════════════

from datetime import datetime
from pathlib import Path
import re

_BRAND_SLUG = {'realprize': 'rp', 'lonestar': 'ls'}
brand_slug = '_'.join(
    _BRAND_SLUG.get(b, re.sub(r'[^a-z0-9]+', '', b.lower())[:6])
    for b in RUN_BRANDS
)
exported_at = datetime.now()
run_ts = exported_at.strftime('%H%M%S')
run_tag = f"{AS_OF_DATE.date()}_{brand_slug}_{EXPERIMENT_TAG}_{run_ts}"

paths = {
    'cv_summary': f'combined_cv_summary_{run_tag}_cv_diagnosis.csv',
    'dist': f'cv_diagnosis_distributions_{run_tag}.csv',
    'dates': f'cv_diagnosis_cohort_dates_{run_tag}.csv',
    'final': f'cv_diagnosis_final_high_cv_{run_tag}.csv',
}
cv_df.to_csv(paths['cv_summary'], index=False)
summary.to_csv(paths['dist'], index=False)
if not date_df.empty:
    date_df.to_csv(paths['dates'], index=False)
final[final_view_cols].to_csv(paths['final'], index=False)

print('Run tag:', run_tag)
print('Saved in working directory:')
for p in paths.values():
    print(' ', p)

run_candidates = [
    Path('/Users/leejerusalmy/Library/CloudStorage/'
         'GoogleDrive-lee@realplayltd.com/My Drive/lee_project/'
         'marketing_goals/runs'),
    Path('/content/drive/MyDrive/lee_project/marketing_goals/runs'),
    Path('/content/drive/My Drive/lee_project/marketing_goals/runs'),
]
drive_runs = next((c for c in run_candidates if c.is_dir()), None)
if drive_runs is not None:
    out_dir = drive_runs / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    cv_df.to_csv(out_dir / 'combined_cv_summary_cv_diagnosis.csv', index=False)
    summary.to_csv(out_dir / 'cv_diagnosis_distributions.csv', index=False)
    if not date_df.empty:
        date_df.to_csv(out_dir / 'cv_diagnosis_cohort_dates.csv', index=False)
    final[final_view_cols].to_csv(out_dir / 'cv_diagnosis_final_high_cv.csv', index=False)
    meta = pd.DataFrame([{
        'run_tag': run_tag,
        'as_of_date': str(AS_OF_DATE.date()),
        'brands': ','.join(RUN_BRANDS),
        'brand_slug': brand_slug,
        'run_ts': run_ts,
        'exported_at': exported_at.isoformat(timespec='seconds'),
        'env': 'colab',
        'experiment_tag': EXPERIMENT_TAG,
        'purpose': 'cv_diagnosis_only',
    }])
    meta.to_csv(out_dir / 'run_meta.csv', index=False)
    print('Saved Drive folder:', out_dir)
else:
    print('Drive runs/ folder not found — working-dir CSVs only.')
'''


def main():
    generic = json.loads(GENERIC.read_text())
    assert not any("WINSOR_ESCALATION" in get_src(generic, i) for i in range(len(generic["cells"])))
    nb = deepcopy(generic)

    # markdown
    set_src(
        nb,
        0,
        """# Marketing Goals — **CV diagnosis** (exploratory)

*Lee Jerusalmy*

Isolated investigation notebook under `experiments/cv_optimization/cv_diagnosis/`.

**Purpose:** understand *why* existing Marketing Goals CV is high on some patches — outliers, broad dispersion, sample size, zeros, skew, time trends, etc.

**Not** a methodology change: does not replace CV, change thresholds/trimming, or modify goals.

Uses the same cohort construction / winsor / weighted CV / date-removal as Combined.  
Pinned `AS_OF_DATE = 2026-08-03` for comparability with other CV experiments.  
Production LS `cv_threshold` kept at **0.175** (existing model logic).

Do **not** confuse with `robust_cv` / `window_escalation` / `winsor_escalation`.
""",
    )

    # config cell
    s4 = get_src(nb, 4)
    s4 = s4.replace(
        "AS_OF_DATE = pd.Timestamp.now().normalize() - pd.Timedelta(days=2)",
        """# CHANGED (temporary for testing): pin AS_OF to match prior CV test runs.
# REVERT for production to: pd.Timestamp.now().normalize() - pd.Timedelta(days=2)
AS_OF_DATE = pd.Timestamp('2026-08-03')""",
    )
    s4 = s4.replace(
        "LOOKBACK_COHORTS = 35\n",
        """LOOKBACK_COHORTS = 35
EXPERIMENT_TAG = 'cv_diagnosis'  # ADDED: distinct runs/ folder

# ADDED: diagnosis thresholds (documented; easy to retune)
NEAR_ZERO_GROWTH = 1e-6      # |growth_ratio| <= this → near-zero at cohort level
NEAR_ZERO_USER_REV = 1e-6    # |user cum revenue at patch end| <= this → near-zero user
TREND_CORR_STRONG = 0.60     # |corr(growth, cohort_date)| >= this → time_trend_flag

# Known interesting cases (auto high-CV detection still primary)
FOCUS_CASES = [
    ('lonestar', 'Blended', '1->7'),
    ('lonestar', 'Web', '1->7'),
    ('lonestar', 'Web', '180->270'),
    ('realprize', 'App', '1->7'),
    ('realprize', 'Blended', '1->7'),
    ('realprize', 'Web', '1->7'),
    ('realprize', 'Web', '7->14'),
    ('realprize', 'Web', '14->30'),
    ('realprize', 'Web', '30->60'),
]
""",
        1,
    )
    # keep LS 0.175 — production
    assert "'cv_threshold': 0.175" in s4
    set_src(nb, 4, s4)

    # replace patch_cv cell
    set_src(nb, 8, NEW_PATCH_CV)

    # Drop organic / goals / old export / preview — replace with diagnosis flow
    # Keep cells 0-9 (through curve builder), 11 has monitors+run_brand — we replace 10-15
    # Cell 10 = organic → stub
    set_src(
        nb,
        10,
        "# ADDED: organic helper skipped in cv_diagnosis (not needed for CV observation diagnosis).\n"
        "print('Organic helpers skipped (cv_diagnosis).')\n",
    )

    # Cell 11 keep run_brand_pipeline for reference but we won't call full pipeline —
    # leave as-is from generic (still useful if someone calls it). No change required.

    # Cell 12 = diagnosis run
    set_src(nb, 12, DIAG_RUN)

    # Cell 13 = analysis
    set_src(nb, 13, DIAG_ANALYSIS)

    # Cell 14 = export
    set_src(nb, 14, DIAG_EXPORT)

    # Cell 15 if exists — clear
    if len(nb["cells"]) > 15:
        set_src(nb, 15, "# (unused in cv_diagnosis)\npass\n")

    for c in nb["cells"]:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1))

    src = "\n".join(get_src(nb, i) for i in range(len(nb["cells"])))
    checks = {
        "AS_OF": "2026-08-03" in src,
        "tag": "cv_diagnosis" in src,
        "LS 0.175 kept": "'cv_threshold': 0.175" in src,
        "no winsor ladder": "WINSOR_ESCALATION" not in src,
        "no robust main": "variability_diagnosis" not in src,
        "NEAR_ZERO": "NEAR_ZERO_GROWTH" in src,
        "date detail": "CV_DIAG_DATE_ROWS" in src,
        "focus": "FOCUS_CASES" in src,
        "final notes": "diagnostic_notes" in src,
        "no goals export main": "combined_goals_" not in src or "DIAGNOSIS" in src,
    }
    for k, ok in checks.items():
        print(("OK" if ok else "FAIL"), k)
    assert all(checks.values())
    print("Wrote", OUT_NB)


if __name__ == "__main__":
    main()
