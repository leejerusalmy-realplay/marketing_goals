#!/usr/bin/env python3
"""Build cv_oos_backtest Colab from generic Combined.

Does NOT touch robust_cv / cv_diagnosis / window_escalation / winsor_escalation / notebooks/.
"""
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


BACKTEST_HELPERS = r'''# ══════════════════════════════════════════════════════════════
# ADDED: walk-forward backtest helpers (framework only)
# Production CV / trim / goal formulas are NOT changed.
#
# Patch-level "Marketing Goal" in this experiment =
#   mean_after from patch_cv_adaptive
#   = weighted mean of kept cohort growth_ratios (ARPU_e / ARPU_s)
# This is exactly the quantity that existing CV summarizes.
# Full day-level goal curves / organic are out of scope here.
# ══════════════════════════════════════════════════════════════

APE_NEAR_ZERO_GOAL = 1e-8  # ADDED: skip APE when |goal| below this


def generate_cutoff_dates(eval_as_of, *, freq_days, span_days, max_test_horizon, max_patch_e):
    """Historical as_of dates with room for training maturity + OOS test maturity.

    Latest cutoff T must allow test cohorts to reach day e by eval_as_of:
      T - e + max_test_horizon + e <= eval_as_of
      => T <= eval_as_of - max_test_horizon
    (plus 1-day slack).
    """
    eval_as_of = pd.Timestamp(eval_as_of).normalize()
    latest = eval_as_of - pd.Timedelta(days=int(max_test_horizon) + 1)
    earliest = latest - pd.Timedelta(days=int(span_days))
    dates = pd.date_range(earliest, latest, freq=f'{int(freq_days)}D')
    return [pd.Timestamp(d).normalize() for d in dates]


def growth_for_cost_date(u_base, daily_user_cums, *, population, s, e, cost_date):
    """Actual cohort growth_ratio for one cost_date (same winsor helper as production).

    Uses only users on that cost_date — no other dates enter the trim window.
    Documented framework choice: single-date winsor (not borrowing future/past dates).
    """
    cost_date = pd.to_datetime(cost_date).date() if not hasattr(cost_date, 'year') else cost_date
    cohort_users = u_base.loc[
        (u_base['population'] == population) & (u_base['cost_date'] == cost_date)
    ][['population', 'cost_date', '__uid__']].copy()
    if cohort_users.empty:
        return None
    trimmed_users, caps = get_trimmed_cohort_and_caps(
        population, cohort_users, daily_user_cums, e
    )
    if trimmed_users.empty:
        return None
    n_users = int(trimmed_users['__uid__'].nunique())
    sum_s = sum_cum_at_idx(daily_user_cums, cohort_users=trimmed_users, idx=s - 1, caps=caps)
    sum_e = sum_cum_at_idx(daily_user_cums, cohort_users=trimmed_users, idx=e - 1, caps=caps)
    if sum_s.empty or sum_e.empty:
        return None
    arpu_s = float(sum_s['sum_cum'].iloc[0]) / n_users if n_users else np.nan
    arpu_e = float(sum_e['sum_cum'].iloc[0]) / n_users if n_users else np.nan
    if not np.isfinite(arpu_s) or arpu_s <= 0 or not np.isfinite(arpu_e):
        return None
    return dict(
        cost_date=cost_date,
        n_users=n_users,
        ARPU_s=arpu_s,
        ARPU_e=arpu_e,
        actual_growth=arpu_e / arpu_s,
    )


def list_candidate_test_dates(u_base, *, population, training_end, n_wanted, e, eval_as_of):
    """Next eligible cost_dates after training_end that are mature by eval_as_of."""
    eval_as_of = pd.Timestamp(eval_as_of).normalize()
    training_end = pd.to_datetime(training_end).date()
    max_cost = (eval_as_of - pd.Timedelta(days=e)).date()
    dates = (
        u_base.loc[
            (u_base['population'] == population)
            & (u_base['cost_date'] > training_end)
            & (u_base['cost_date'] <= max_cost),
            'cost_date'
        ]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    return dates[: int(n_wanted)]


def summarize_errors(actuals, goal):
    """Aggregate OOS errors; APE skipped when |goal| ~ 0."""
    actuals = np.asarray(actuals, dtype=float)
    actuals = actuals[np.isfinite(actuals)]
    out = dict(
        n_test_cohorts=int(actuals.size),
        test_mae=None, test_median_ae=None,
        test_mape=None, test_median_ape=None,
        test_rmse=None, test_bias=None,
    )
    if actuals.size == 0 or goal is None or not np.isfinite(goal):
        return out
    err = actuals - float(goal)
    ae = np.abs(err)
    out['test_mae'] = float(np.mean(ae))
    out['test_median_ae'] = float(np.median(ae))
    out['test_rmse'] = float(np.sqrt(np.mean(err ** 2)))
    out['test_bias'] = float(np.mean(err))
    if abs(float(goal)) > APE_NEAR_ZERO_GOAL:
        ape = ae / abs(float(goal))
        out['test_mape'] = float(np.mean(ape))
        out['test_median_ape'] = float(np.median(ape))
    return out


def run_walkforward_backtest(
    brand_key,
    users_df,
    revenue_df,
    *,
    cutoff_dates,
    eval_as_of,
    test_horizons,
    debug=False,
):
    """For each historical cutoff T: run existing patch CV path, freeze mean_after, score OOS."""
    cfg = BRAND_CONFIGS[brand_key]
    apply_brand_globals(cfg)
    brand = cfg['brand']
    rows = []
    point_rows = []  # per test cohort date

    # Precompute cums once (data is historical; eligibility enforced via as_of in patch_cv)
    pops = list(cfg['populations'])
    u_pop, daily_pop = build_user_revenue_cums(
        users_df.loc[users_df['population'].isin(pops)].copy(),
        revenue_df,
        max_day=365,
    )
    users_blend = users_df.copy()
    users_blend['population'] = 'Blended'
    u_blend, daily_blend = build_user_revenue_cums(users_blend, revenue_df, max_day=365)

    for T in cutoff_dates:
        T = pd.Timestamp(T).normalize()
        if debug:
            print(f'\n[{brand}] cutoff as_of={T.date()}')

        # Existing methodology path at time T (per-pop + blended)
        global POPULATIONS
        POPULATIONS = list(cfg['populations'])
        cv_pop, _ = build_all_populations(
            u_pop, daily_pop, as_of_date=T, extrapolate_tail=False, debug=debug,
        )
        POPULATIONS = ['Blended']
        try:
            cv_blend, _ = build_all_populations(
                u_blend, daily_blend, as_of_date=T, extrapolate_tail=False, debug=debug,
            )
        finally:
            POPULATIONS = list(cfg['populations'])

        cv_t = pd.concat(
            [x for x in [cv_pop, cv_blend] if x is not None and not x.empty],
            ignore_index=True,
        )
        if cv_t.empty:
            continue

        for _, st in cv_t.iterrows():
            pop = st['population']
            patch = st['patch']
            s, e = map(int, patch.split('->'))
            goal = st.get('mean_after')
            training_start = st.get('cohort_start')
            training_end = st.get('cohort_end')
            u_base = u_blend if pop == 'Blended' else u_pop
            daily = daily_blend if pop == 'Blended' else daily_pop

            for h in test_horizons:
                test_dates = list_candidate_test_dates(
                    u_base, population=pop, training_end=training_end,
                    n_wanted=h, e=e, eval_as_of=eval_as_of,
                )
                actuals = []
                for d in test_dates:
                    g = growth_for_cost_date(
                        u_base, daily, population=pop, s=s, e=e, cost_date=d,
                    )
                    if g is None:
                        continue
                    actuals.append(g['actual_growth'])
                    if goal is not None and np.isfinite(goal):
                        ae = abs(g['actual_growth'] - float(goal))
                        ape = (ae / abs(float(goal))) if abs(float(goal)) > APE_NEAR_ZERO_GOAL else np.nan
                        point_rows.append({
                            'brand': brand,
                            'population': pop,
                            'patch': patch,
                            'cutoff_as_of': str(T.date()),
                            'training_start': training_start,
                            'training_end': training_end,
                            'goal': float(goal) if goal is not None and np.isfinite(goal) else None,
                            'cv_after': st.get('cv_after'),
                            'flagged': st.get('flagged'),
                            'test_horizon': int(h),
                            'test_cost_date': str(g['cost_date']),
                            'actual_growth': g['actual_growth'],
                            'abs_error': ae,
                            'ape': ape if np.isfinite(ape) else None,
                            'signed_error': g['actual_growth'] - float(goal),
                            'n_test_users': g['n_users'],
                        })

                err = summarize_errors(actuals, goal)
                # insufficient future data → report, do not fill
                rows.append({
                    'brand': brand,
                    'population': pop,
                    'patch': patch,
                    'cutoff_as_of': str(T.date()),
                    'training_start': training_start,
                    'training_end': training_end,
                    'n_training_cohorts': st.get('n_cohort_dates_total'),
                    'n_training_cohorts_kept': st.get('n_cohort_dates_kept'),
                    'n_training_users': st.get('n_users_post_trim'),
                    'goal': float(goal) if goal is not None and np.isfinite(float(goal) if goal is not None else np.nan) else None,
                    'cv_before': st.get('cv_before'),
                    'cv_after': st.get('cv_after'),
                    'flagged_using_existing_logic': bool(st.get('flagged')),
                    'cv_threshold_used': float(CV_THRESHOLD),
                    'test_horizon': int(h),
                    'n_test_dates_available': len(test_dates),
                    'insufficient_test_data': len(actuals) < int(h),
                    **err,
                })

    return pd.DataFrame(rows), pd.DataFrame(point_rows)


print('Walk-forward backtest helpers defined.')
'''

BACKTEST_RUN = r'''# ══════════════════════════════════════════════════════════════
# WALK-FORWARD BACKTEST RUN
# ══════════════════════════════════════════════════════════════

eval_as_of = AS_OF_DATE  # pinned evaluation "today" for maturity of OOS cohorts
max_e = max(e for _, e in PATCHES)
cutoff_dates = generate_cutoff_dates(
    eval_as_of,
    freq_days=CUTOFF_FREQ_DAYS,
    span_days=CUTOFF_SPAN_DAYS,
    max_test_horizon=max(TEST_HORIZONS),
    max_patch_e=max_e,
)
print(f'EVAL_AS_OF (maturity ceiling) = {eval_as_of.date()}')
print(f'Cutoffs: n={len(cutoff_dates)}  first={cutoff_dates[0].date()}  last={cutoff_dates[-1].date()}')
print(f'TEST_HORIZONS = {TEST_HORIZONS}  CUTOFF_FREQ_DAYS = {CUTOFF_FREQ_DAYS}')
print('Look-ahead controls:')
print('  - training window via patch_cv_adaptive(as_of=T) only')
print('  - test dates strictly > training_end and mature by EVAL_AS_OF')
print('  - no future dates in trim/CV/goal at time T')

wf_parts = []
pt_parts = []
brand_cache = {}

for brand_key in RUN_BRANDS:
    cfg = BRAND_CONFIGS[brand_key]
    # Deep SQL floor: history for earliest cutoff + longest patch + lookback + slack
    # load_brand_tables uses LOOKBACK_COHORTS; temporarily widen floor via as_of span
    users_df, revenue_df = load_brand_tables(cfg, as_of_date=eval_as_of)
    # Extra safety: drop any revenue/users after eval_as_of (should already be constrained)
    if 'date' in revenue_df.columns:
        revenue_df = revenue_df.loc[
            pd.to_datetime(revenue_df['date'], errors='coerce') <= eval_as_of
        ].copy()
    brand_cache[brand_key] = (users_df, revenue_df)
    print(f'\n=== BACKTEST {brand_key}  users={len(users_df):,} rev_rows={len(revenue_df):,} ===')
    wf_b, pt_b = run_walkforward_backtest(
        brand_key, users_df, revenue_df,
        cutoff_dates=cutoff_dates,
        eval_as_of=eval_as_of,
        test_horizons=TEST_HORIZONS,
        debug=False,
    )
    if not wf_b.empty:
        wf_parts.append(wf_b)
    if not pt_b.empty:
        pt_parts.append(pt_b)
    print(f'  window-rows={len(wf_b):,}  point-rows={len(pt_b):,}')

wf_df = pd.concat(wf_parts, ignore_index=True) if wf_parts else pd.DataFrame()
pt_df = pd.concat(pt_parts, ignore_index=True) if pt_parts else pd.DataFrame()

# Primary analysis horizon (configurable)
PRIMARY_H = PRIMARY_TEST_HORIZON
wf_primary = wf_df.loc[wf_df['test_horizon'] == PRIMARY_H].copy() if not wf_df.empty else wf_df

print('\n' + '=' * 60)
print('WALK-FORWARD COMPLETE')
print(f'  experiment          = {EXPERIMENT_TAG}')
print(f'  window rows         = {len(wf_df):,}')
print(f'  point rows          = {len(pt_df):,}')
print(f'  primary test_horizon= {PRIMARY_H}')
print(f'  primary rows        = {len(wf_primary):,}')
if not wf_df.empty:
    print('  insufficient_test_data rate:',
          float(wf_df['insufficient_test_data'].mean()))
print('=' * 60)
'''

BACKTEST_ANALYSIS = r'''# ══════════════════════════════════════════════════════════════
# ANALYSIS — Does CV predict OOS goal error?
# ══════════════════════════════════════════════════════════════

import matplotlib.pyplot as plt

assert not wf_df.empty, 'wf_df empty — run backtest cell first'

# Use rows with at least 1 OOS observation
W = wf_primary.loc[wf_primary['n_test_cohorts'] > 0].copy()
print(f'Primary horizon H={PRIMARY_H}: usable windows = {len(W)} / {len(wf_primary)}')

ERR = 'test_median_ae'  # primary error measure (robust to outliers); also report MAE/RMSE

# ── 4) Correlations CV vs error ──
print('\n=== CV vs future prediction error (correlations) ===')

def corr_block(df, label):
    d = df.dropna(subset=['cv_after', ERR])
    if len(d) < 5:
        print(f'{label}: insufficient n={len(d)}')
        return
    pear = d['cv_after'].corr(d[ERR], method='pearson')
    spear = d['cv_after'].corr(d[ERR], method='spearman')
    print(f'{label}: n={len(d)}  Pearson({ERR})={pear:.3f}  Spearman={spear:.3f}')
    for col in ['test_mae', 'test_rmse', 'test_median_ape', 'test_mape']:
        if col in d.columns and d[col].notna().sum() >= 5:
            print(f'    vs {col}: pearson={d["cv_after"].corr(d[col], method="pearson"):.3f}  '
                  f'spearman={d["cv_after"].corr(d[col], method="spearman"):.3f}')

corr_block(W, 'OVERALL')
for patch in [f'{a}->{b}' for a, b in PATCHES]:
    corr_block(W.loc[W['patch'] == patch], f'patch {patch}')

# ── 5) Threshold 0.15 ──
print('\n=== Existing ~15% threshold: CV<=0.15 vs CV>0.15 ===')

def threshold_compare(df, label):
    d = df.dropna(subset=['cv_after', ERR]).copy()
    if d.empty:
        print(label, '(empty)')
        return None
    d['cv_gt_15'] = d['cv_after'] > 0.15
    rows = []
    for flag, name in [(False, 'CV<=0.15'), (True, 'CV>0.15')]:
        sub = d.loc[d['cv_gt_15'] == flag]
        rows.append({
            'group': name,
            'n': len(sub),
            'median_error': sub[ERR].median() if len(sub) else None,
            'mean_error': sub[ERR].mean() if len(sub) else None,
            'p75_error': sub[ERR].quantile(0.75) if len(sub) else None,
            'p90_error': sub[ERR].quantile(0.90) if len(sub) else None,
            'median_bias': sub['test_bias'].median() if len(sub) else None,
            'mean_bias': sub['test_bias'].mean() if len(sub) else None,
        })
    out = pd.DataFrame(rows)
    print(f'\n-- {label} --')
    print(out.to_string(index=False))
    return out

threshold_compare(W, 'OVERALL')
for patch in [f'{a}->{b}' for a, b in PATCHES]:
    threshold_compare(W.loc[W['patch'] == patch], f'patch {patch}')

# ── 6) Patch-specific summary ──
print('\n=== Patch-specific summary ===')
patch_order = [f'{a}->{b}' for a, b in PATCHES]
patch_rows = []
for patch in patch_order:
    sub = W.loc[W['patch'] == patch].dropna(subset=['cv_after'])
    if sub.empty:
        continue
    le = sub.loc[sub['cv_after'] <= 0.15, ERR]
    gt = sub.loc[sub['cv_after'] > 0.15, ERR]
    d = sub.dropna(subset=[ERR])
    patch_rows.append({
        'patch': patch,
        'median_cv': sub['cv_after'].median(),
        'p75_cv': sub['cv_after'].quantile(0.75),
        'p90_cv': sub['cv_after'].quantile(0.90),
        'median_oos_error': d[ERR].median() if len(d) else None,
        'p75_oos_error': d[ERR].quantile(0.75) if len(d) else None,
        'p90_oos_error': d[ERR].quantile(0.90) if len(d) else None,
        'corr_cv_error_pearson': d['cv_after'].corr(d[ERR], method='pearson') if len(d) >= 5 else None,
        'corr_cv_error_spearman': d['cv_after'].corr(d[ERR], method='spearman') if len(d) >= 5 else None,
        'pct_windows_cv_gt_15': float((sub['cv_after'] > 0.15).mean()),
        'median_error_cv_le_15': le.median() if len(le) else None,
        'median_error_cv_gt_15': gt.median() if len(gt) else None,
        'n_backtests': len(sub),
    })
patch_summary = pd.DataFrame(patch_rows)
print(patch_summary.to_string(index=False))

# ── 7) CV buckets ──
print('\n=== Error by CV bucket ===')
bins = [-np.inf, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, np.inf]
labels = ['<5%', '5-10%', '10-15%', '15-20%', '20-25%', '25-30%', '>30%']
Wb = W.dropna(subset=['cv_after', ERR]).copy()
Wb['cv_bucket'] = pd.cut(Wb['cv_after'], bins=bins, labels=labels)

def bucket_table(df, label):
    print(f'\n-- {label} --')
    if df.empty:
        print('(empty)')
        return
    g = df.groupby('cv_bucket', observed=True).agg(
        n=('cv_after', 'count'),
        median_error=(ERR, 'median'),
        p75_error=(ERR, lambda s: s.quantile(0.75)),
        p90_error=(ERR, lambda s: s.quantile(0.90)),
        median_bias=('test_bias', 'median'),
    )
    print(g.to_string())

bucket_table(Wb, 'OVERALL')
for patch in ['1->7', '7->14', '14->30', '30->60', '60->90', '90->120']:
    bucket_table(Wb.loc[Wb['patch'] == patch], f'patch {patch}')

# ── 8) Special focus 1->7 ──
print('\n=== 1->7 deep dive ===')
w17 = wf_df.loc[(wf_df['patch'] == '1->7') & (wf_df['n_test_cohorts'] > 0)].copy()
# pivot horizons
piv = (
    w17.pivot_table(
        index=['brand', 'population', 'cutoff_as_of', 'goal', 'cv_after'],
        columns='test_horizon',
        values=ERR,
        aggfunc='first',
    )
    .reset_index()
)
piv = piv.rename(columns={7: 'next_7_error', 14: 'next_14_error', 30: 'next_30_error'})
print(piv.sort_values(['brand', 'population', 'cutoff_as_of']).to_string(index=False))

def q_band(df, lo, hi, name):
    sub = df.loc[(df['cv_after'] > lo) & (df['cv_after'] <= hi) & (df['test_horizon'] == PRIMARY_H)]
    print(f'\nQuestion {name}: CV in ({lo:.0%}, {hi:.0%}]  n={len(sub)}')
    if sub.empty:
        print('  insufficient data')
        return
    print(f"  median {ERR}={sub[ERR].median():.4f}  p75={sub[ERR].quantile(0.75):.4f}  "
          f"p90={sub[ERR].quantile(0.90):.4f}  mean={sub[ERR].mean():.4f}")

w17p = w17.loc[w17['test_horizon'] == PRIMARY_H]
q_band(w17p, 0.15, 0.20, 'A 15-20%')
q_band(w17p, 0.20, 0.25, 'B 20-25%')
q_band(w17p, 0.25, 1.00, 'C >25%')
print('\nQuestion D: look at bucket table for 1->7 — only call a cliff if error jumps materially.')

# ── 9) Population / sample size ──
print('\n=== By brand × population (primary horizon) ===')
print(
    W.groupby(['brand', 'population'], observed=True)
     .agg(n=('cv_after', 'count'),
          median_cv=('cv_after', 'median'),
          median_err=(ERR, 'median'),
          pearson=('cv_after', lambda s: s.corr(W.loc[s.index, ERR], method='pearson') if len(s)>=5 else np.nan))
     .to_string()
)

print('\n=== Similar CV, large vs small N (exploratory) ===')
W2 = W.dropna(subset=['cv_after', ERR, 'n_training_users']).copy()
W2['cv_band'] = pd.cut(W2['cv_after'], bins=[-np.inf, 0.10, 0.15, 0.20, 0.30, np.inf],
                       labels=['<=10%', '10-15%', '15-20%', '20-30%', '>30%'])
W2['n_band'] = pd.cut(W2['n_training_users'], bins=[-np.inf, 2000, 10000, np.inf],
                      labels=['small<=2k', 'mid', 'large>10k'])
print(
    W2.groupby(['cv_band', 'n_band'], observed=True)
      .agg(n=(ERR, 'count'), median_err=(ERR, 'median'))
      .to_string()
)
print('RealPrize Web:')
print(
    W2.loc[(W2['brand'] == 'realprize') & (W2['population'] == 'Web'),
           ['patch', 'cv_after', 'n_training_users', ERR, 'flagged_using_existing_logic']]
    .sort_values(ERR, ascending=False)
    .head(30)
    .to_string(index=False)
)

# ── 10) Goal stability ──
print('\n=== Goal stability across cutoffs ===')
stab_rows = []
for (brand, pop, patch), g in W.groupby(['brand', 'population', 'patch']):
    goals = g['goal'].dropna()
    if len(goals) < 3:
        continue
    stab_rows.append({
        'brand': brand, 'population': pop, 'patch': patch,
        'n_windows': len(goals),
        'goal_median': goals.median(),
        'goal_cv': float(goals.std(ddof=0) / goals.mean()) if goals.mean() else None,
        'goal_iqr': float(goals.quantile(0.75) - goals.quantile(0.25)),
        'goal_range': float(goals.max() - goals.min()),
        'median_cv_after': g['cv_after'].median(),
    })
stability_df = pd.DataFrame(stab_rows)
print(stability_df.sort_values('goal_cv', ascending=False).to_string(index=False))

# ── 11) Plots ──
print('\n=== Plots ===')
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(W['cv_after'], W[ERR], alpha=0.55, s=25)
ax.axvline(0.15, color='red', ls='--', label='CV=0.15')
ax.set_xlabel('cv_after (in-sample)')
ax.set_ylabel(f'{ERR} (OOS, H={PRIMARY_H})')
ax.set_title('CV after → out-of-sample error')
ax.legend()
plt.tight_layout()
plt.show()

focus_patches = ['1->7', '7->14', '14->30', '30->60', '60->90', '90->120']
fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=False, sharey=False)
for i, patch in enumerate(focus_patches):
    ax = axes[i // 3][i % 3]
    sub = W.loc[W['patch'] == patch]
    ax.scatter(sub['cv_after'], sub[ERR], alpha=0.6, s=20)
    ax.axvline(0.15, color='red', ls='--', lw=1)
    ax.set_title(patch)
    ax.set_xlabel('cv_after')
    ax.set_ylabel(ERR)
plt.suptitle('CV vs OOS error by patch')
plt.tight_layout()
plt.show()

# Error by CV bucket boxplot
fig, ax = plt.subplots(figsize=(9, 5))
order = [l for l in labels if l in set(Wb['cv_bucket'].astype(str))]
data = [Wb.loc[Wb['cv_bucket'] == l, ERR].dropna().values for l in labels]
ax.boxplot(data, labels=labels, showfliers=False)
ax.set_title(f'OOS {ERR} by CV bucket (primary H={PRIMARY_H})')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.show()

# Rolling goal stability examples: focus cases
FOCUS_PLOT = [
    ('realprize', 'Web', '1->7'),
    ('realprize', 'Web', '14->30'),
    ('lonestar', 'Web', '1->7'),
    ('lonestar', 'Blended', '1->7'),
]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for i, (brand, pop, patch) in enumerate(FOCUS_PLOT):
    ax = axes[i // 2][i % 2]
    sub = W.loc[(W['brand'] == brand) & (W['population'] == pop) & (W['patch'] == patch)].copy()
    if sub.empty:
        ax.set_title(f'{brand} {pop} {patch} (no data)')
        continue
    sub['cutoff_dt'] = pd.to_datetime(sub['cutoff_as_of'])
    sub = sub.sort_values('cutoff_dt')
    ax.plot(sub['cutoff_dt'], sub['goal'], marker='o', label='goal (mean_after)')
    ax2 = ax.twinx()
    ax2.plot(sub['cutoff_dt'], sub['cv_after'], color='orange', alpha=0.7, label='cv_after')
    ax.set_title(f'{brand} | {pop} | {patch}')
    ax.tick_params(axis='x', rotation=45)
    ax.set_ylabel('goal')
    ax2.set_ylabel('cv_after')
plt.suptitle('Rolling goal stability (left axis) vs CV (right)')
plt.tight_layout()
plt.show()

# 1->7 deep dive scatter
fig, ax = plt.subplots(figsize=(7, 5))
sub = W.loc[W['patch'] == '1->7']
ax.scatter(sub['cv_after'], sub[ERR], alpha=0.65)
ax.axvline(0.15, color='red', ls='--')
ax.axvline(0.20, color='grey', ls=':')
ax.axvline(0.25, color='grey', ls=':')
ax.set_title('1->7: CV after vs OOS error')
ax.set_xlabel('cv_after')
ax.set_ylabel(ERR)
plt.tight_layout()
plt.show()
'''

BACKTEST_FINAL = r'''# ══════════════════════════════════════════════════════════════
# FINAL DECISION TABLE + answers (descriptive only)
# ══════════════════════════════════════════════════════════════

def _interpret(row):
    n = row['n_backtests']
    if n is None or n < 8:
        return 'Insufficient historical observations'
    sp = row['corr_cv_error_spearman']
    pe = row['corr_cv_error_pearson']
    corr = sp if sp is not None and np.isfinite(sp) else pe
    le = row['median_error_cv_le_15']
    gt = row['median_error_cv_gt_15']
    notes = []
    if corr is None or not np.isfinite(corr):
        notes.append('Weak/unclear CV–error relationship')
    elif corr >= 0.45:
        notes.append('Higher CV strongly associated with worse future prediction')
    elif corr >= 0.25:
        notes.append('Moderate relationship')
    elif corr >= 0.10:
        notes.append('Weak relationship')
    else:
        notes.append('No meaningful relationship detected')
    if le is not None and gt is not None and np.isfinite(le) and np.isfinite(gt):
        if gt > le * 1.25:
            notes.append('CV>15% group has materially higher median OOS error')
        elif gt <= le * 1.10:
            notes.append('CV >15% does not materially reduce predictive accuracy')
    return ' | '.join(notes)

final = patch_summary.copy()
final['interpretation'] = final.apply(_interpret, axis=1)
final_cols = [
    'patch', 'median_cv', 'p90_cv', 'median_oos_error', 'p90_oos_error',
    'corr_cv_error_pearson', 'corr_cv_error_spearman',
    'median_error_cv_le_15', 'median_error_cv_gt_15', 'n_backtests', 'interpretation',
]
print('=== FINAL summary by patch (primary OOS horizon) ===')
print(final[final_cols].to_string(index=False))

# Cases: high CV but good OOS / low CV but bad OOS
print('\n=== High CV but relatively low OOS error (top examples) ===')
hi = W.loc[W['cv_after'] > 0.15].copy()
if not hi.empty:
    hi['err_rank'] = hi[ERR].rank(pct=True)
    print(hi.nsmallest(15, ERR)[
        ['brand', 'population', 'patch', 'cutoff_as_of', 'cv_after', 'goal', ERR, 'test_bias']
    ].to_string(index=False))

print('\n=== Low CV but relatively high OOS error (top examples) ===')
lo = W.loc[W['cv_after'] <= 0.10].copy()
if not lo.empty:
    print(lo.nlargest(15, ERR)[
        ['brand', 'population', 'patch', 'cutoff_as_of', 'cv_after', 'goal', ERR, 'test_bias']
    ].to_string(index=False))

print('\n=== Concise answers (evidence from this backtest only) ===')
# 1
d = W.dropna(subset=['cv_after', ERR])
sp = d['cv_after'].corr(d[ERR], method='spearman') if len(d) >= 5 else np.nan
print(f'1) Does CV predict future goal error?  Overall Spearman({ERR})={sp:.3f} on n={len(d)}. '
      f'See per-patch correlations in the table.')
# 2
le = d.loc[d['cv_after'] <= 0.15, ERR].median()
gt = d.loc[d['cv_after'] > 0.15, ERR].median()
print(f'2) Does 15% threshold separate reliability?  median {ERR}: CV<=15% → {le:.4f} ; CV>15% → {gt:.4f}')
# 3
print('3) Relationship by patch: see FINAL table (corr + interpretation). Early vs mature often differ.')
# 4
s17 = final.loc[final['patch'] == '1->7']
if not s17.empty:
    r = s17.iloc[0]
    print(f"4) 1->7: median_cv={r['median_cv']:.3f}, corr_spearman={r['corr_cv_error_spearman']}, "
          f"interp={r['interpretation']}")
else:
    print('4) 1->7: insufficient rows')
# 5-6 already printed examples
print('5) High-CV but accurate cases: see table above (if any).')
print('6) Low-CV but inaccurate cases: see table above (if any).')
# 7
early = final.loc[final['patch'].isin(['1->7', '7->14', '14->30'])]
mature = final.loc[final['patch'].isin(['90->120', '120->150', '150->180', '180->270', '270->365'])]
print(
    '7) Patch-specific CV expectations?  Compare early vs mature median_cv / corr in FINAL table. '
    'Only treat as evidence for eventually considering patch-specific expectations if early patches '
    'show high natural CV without matching OOS-error penalty. Do NOT change production from this notebook.'
)
print('\nReminder: this experiment does not change Marketing Goals methodology.')
'''

BACKTEST_EXPORT = r'''# ══════════════════════════════════════════════════════════════
# EXPORT — backtest CSVs (distinct experiment_tag; no overwrites)
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

files = {
    'windows': f'cv_oos_backtest_windows_{run_tag}.csv',
    'points': f'cv_oos_backtest_points_{run_tag}.csv',
    'patch_summary': f'cv_oos_backtest_patch_summary_{run_tag}.csv',
    'final': f'cv_oos_backtest_final_{run_tag}.csv',
}
wf_df.to_csv(files['windows'], index=False)
pt_df.to_csv(files['points'], index=False)
patch_summary.to_csv(files['patch_summary'], index=False)
final[final_cols].to_csv(files['final'], index=False)

print('Run tag:', run_tag)
for p in files.values():
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
    wf_df.to_csv(out_dir / 'cv_oos_backtest_windows.csv', index=False)
    pt_df.to_csv(out_dir / 'cv_oos_backtest_points.csv', index=False)
    patch_summary.to_csv(out_dir / 'cv_oos_backtest_patch_summary.csv', index=False)
    final[final_cols].to_csv(out_dir / 'cv_oos_backtest_final.csv', index=False)
    pd.DataFrame([{
        'run_tag': run_tag,
        'as_of_date': str(AS_OF_DATE.date()),
        'brands': ','.join(RUN_BRANDS),
        'experiment_tag': EXPERIMENT_TAG,
        'primary_test_horizon': PRIMARY_H,
        'cutoff_freq_days': CUTOFF_FREQ_DAYS,
        'cutoff_span_days': CUTOFF_SPAN_DAYS,
        'n_cutoffs': len(cutoff_dates),
        'exported_at': exported_at.isoformat(timespec='seconds'),
        'purpose': 'cv_predicts_oos_goal_error_walkforward',
        'goal_definition': 'patch mean_after (weighted mean growth_ratio after CV cleanup)',
    }]).to_csv(out_dir / 'run_meta.csv', index=False)
    print('Saved Drive folder:', out_dir)
else:
    print('Drive runs/ not mounted — working-dir CSVs only.')
'''


def main():
    generic = json.loads(GENERIC.read_text())
    nb = deepcopy(generic)

    set_src(
        nb,
        0,
        """# Marketing Goals — **CV → OOS predictive backtest**

*Lee Jerusalmy*

Isolated experiment: `experiments/cv_optimization/cv_oos_backtest/`.

**Question:** Does high in-sample CV mean the Marketing Goal is unreliable out-of-sample?

Walk-forward / rolling historical backtest of the **existing** methodology (no look-ahead).  
Does **not** change CV, trim, windows, thresholds, or goal formulas.

**Patch goal definition (documented):** `mean_after` from `patch_cv_adaptive`  
= weighted mean of kept cohort `growth_ratio = ARPU_e/ARPU_s` — the quantity existing CV describes.

Other experiments (`robust_cv`, `cv_diagnosis`, …) are untouched.
""",
    )

    s4 = get_src(nb, 4)
    s4 = s4.replace(
        "AS_OF_DATE = pd.Timestamp.now().normalize() - pd.Timedelta(days=2)",
        """# CHANGED (temporary): evaluation "today" for OOS maturity ceiling + comparability
# REVERT for production rolling logic later.
AS_OF_DATE = pd.Timestamp('2026-08-03')""",
    )
    s4 = s4.replace(
        "LOOKBACK_COHORTS = 35\n",
        """LOOKBACK_COHORTS = 35  # unchanged production lookback
EXPERIMENT_TAG = 'cv_oos_backtest'

# ADDED: walk-forward knobs (framework only — not production model knobs)
TEST_HORIZONS = [7, 14, 30]          # next N cohort dates after training_end
PRIMARY_TEST_HORIZON = 14            # main analysis horizon
CUTOFF_FREQ_DAYS = 14                # biweekly historical cutoffs (raise runtime if weekly)
CUTOFF_SPAN_DAYS = 180               # how far back cutoffs extend
""",
        1,
    )
    # Keep LS 0.175 — existing methodology
    assert "'cv_threshold': 0.175" in s4
    set_src(nb, 4, s4)

    # Widen SQL floor for earliest cutoffs: use CUTOFF_SPAN + max test + lookback slack
    s5 = get_src(nb, 5)
    old_floor = """    sql_floor = (
        as_of_date - pd.Timedelta(days=max(GOAL_HORIZONS) + LOOKBACK_COHORTS + 5)
    ).date()"""
    new_floor = """    # ADDED (backtest framework): deeper SQL floor so early cutoffs have history.
    # Does not change patch lookback (still LOOKBACK_COHORTS=35 at each cutoff).
    _extra = int(globals().get('CUTOFF_SPAN_DAYS', 0)) + int(max(globals().get('TEST_HORIZONS', [30]))) + 40
    sql_floor = (
        as_of_date - pd.Timedelta(days=max(GOAL_HORIZONS) + LOOKBACK_COHORTS + _extra)
    ).date()"""
    assert old_floor in s5
    s5 = s5.replace(old_floor, new_floor)
    set_src(nb, 5, s5)

    # Insert helpers after patch_cv cell (cell 8) by appending to cell 8
    s8 = get_src(nb, 8)
    assert "def patch_cv_adaptive" in s8
    s8 = s8.rstrip() + "\n\n" + BACKTEST_HELPERS
    set_src(nb, 8, s8)

    # Skip organic
    set_src(
        nb,
        10,
        "# Organic skipped in cv_oos_backtest (patch growth goal only).\n"
        "print('Organic helpers skipped (cv_oos_backtest).')\n",
    )

    # Replace run / preview / export
    set_src(nb, 12, BACKTEST_RUN)
    set_src(nb, 13, BACKTEST_ANALYSIS)
    set_src(nb, 14, BACKTEST_FINAL)

    # Add export as new cell 15 (replace if exists)
    if len(nb["cells"]) > 15:
        set_src(nb, 15, BACKTEST_EXPORT)
    else:
        nb["cells"].append(
            {
                "cell_type": "code",
                "metadata": {},
                "source": BACKTEST_EXPORT.splitlines(keepends=True)
                if BACKTEST_EXPORT.endswith("\n")
                else (BACKTEST_EXPORT + "\n").splitlines(keepends=True),
                "outputs": [],
                "execution_count": None,
            }
        )

    for c in nb["cells"]:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1))

    src = "\n".join(get_src(nb, i) for i in range(len(nb["cells"])))
    checks = {
        "tag": "cv_oos_backtest" in src,
        "walkforward": "run_walkforward_backtest" in src,
        "no look-ahead comment": "no future dates in trim" in src.lower() or "Look-ahead controls" in src,
        "LS 0.175": "'cv_threshold': 0.175" in src,
        "lookback 35": "LOOKBACK_COHORTS = 35" in src,
        "test horizons": "TEST_HORIZONS = [7, 14, 30]" in src,
        "threshold test": "CV<=0.15" in src,
        "1->7": "1->7 deep dive" in src,
        "final answers": "Concise answers" in src,
        "no robust diagnosis overwrite": "variability_logging_zzz" not in src,
    }
    for k, ok in checks.items():
        print(("OK" if ok else "FAIL"), k)
    assert all(checks.values())
    print("Wrote", OUT_NB)


if __name__ == "__main__":
    main()
