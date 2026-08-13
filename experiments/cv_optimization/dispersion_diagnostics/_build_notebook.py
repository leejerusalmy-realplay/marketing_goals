#!/usr/bin/env python3
"""Build dispersion_diagnostics Colab from generic Combined.

Does NOT touch: cv_oos_backtest, cv_diagnosis, robust_cv, generic notebooks/.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERIC = ROOT / "notebooks" / "Marketing_Goals_Combined_RP_LS_Colab.ipynb"
OUT_DIR = Path(__file__).resolve().parent
OUT_NB = OUT_DIR / "marketing_goals_dispersion_diagnostics.ipynb"


def get_src(nb, i):
    return "".join(nb["cells"][i].get("source", []))


def set_src(nb, i, new_src: str):
    if not new_src.endswith("\n"):
        new_src += "\n"
    nb["cells"][i]["source"] = new_src.splitlines(keepends=True)
    if nb["cells"][i]["cell_type"] == "code":
        nb["cells"][i]["outputs"] = []
        nb["cells"][i]["execution_count"] = None


TITLE_MD = """# Marketing Goals — **dispersion diagnostics** (exploratory)

*Lee Jerusalmy*

Isolated notebook under `experiments/cv_optimization/dispersion_diagnostics/`.

**Question:** when existing CV is high, is variability (A) tail-driven, (B) broad in the center, or (C) multiplicative / asymmetric on the original scale?

**Not** a methodology change: does not replace CV, invent 15%-style thresholds for MAD/IQR, change trimming, or modify goals.

Uses the **same** post-trim cohort `growth_ratio`s that feed `cv_after`.  
Pinned `AS_OF_DATE = 2026-08-03`. Production LS flag thr kept at **0.175**.

Separate from `cv_oos_backtest` (predictive) and from `robust_cv` (MAD×1.4826 as CV alternative).
"""


INSTRUMENT_HEADER = """# ══════════════════════════════════════════════════════════════
# ADAPTIVE CV ANALYSIS — persistent trim
# + DISPERSION instrumentation (same CV math; capture after-trim rows)
# ══════════════════════════════════════════════════════════════

# Accumulated during dispersion run (reset in the RUN cell)
DISP_DATE_ROWS = []


"""

INSTRUMENT_BEFORE_RETURN = """
    # ── DISPERSION ONLY (does not affect CV / flagged) ──
    brand = globals().get('ACTIVE_BRAND', None)
    removed_set = set(removed)
    detail = remaining[['population', 'cost_date', 'N_users', 'sum_cum_s',
                        'sum_cum_e', 'ARPU_s', 'ARPU_e', 'growth_ratio']].copy()
    detail.insert(0, 'brand', brand)
    detail.insert(2, 'patch', f'{s}->{e}')
    detail = detail.rename(columns={
        'cost_date': 'cohort_date',
        'growth_ratio': 'cohort_metric_used_for_cv',
        'N_users': 'n_users',
    })
    detail['was_removed_by_existing_trim'] = False
    # also keep removed dates for viz context
    removed_detail = patch.loc[patch['cost_date'].isin(removed_set),
                               ['population', 'cost_date', 'N_users', 'sum_cum_s',
                                'sum_cum_e', 'ARPU_s', 'ARPU_e', 'growth_ratio']].copy()
    if not removed_detail.empty:
        removed_detail.insert(0, 'brand', brand)
        removed_detail.insert(2, 'patch', f'{s}->{e}')
        removed_detail = removed_detail.rename(columns={
            'cost_date': 'cohort_date',
            'growth_ratio': 'cohort_metric_used_for_cv',
            'N_users': 'n_users',
        })
        removed_detail['was_removed_by_existing_trim'] = True
        detail = pd.concat([detail, removed_detail], ignore_index=True)
    detail['cv_before'] = float(cv_before) if not np.isnan(cv_before) else None
    detail['cv_after'] = float(cv_after) if not np.isnan(cv_after) else None
    detail['flagged'] = bool(flagged)
    detail['n_users_post_trim'] = n_users_post_trim
    DISP_DATE_ROWS.append(detail)

"""


DISP_RUN = r'''# ══════════════════════════════════════════════════════════════
# DISPERSION RUN — CV observations only (no organic / goals)
# Same Part 1+2 path as Marketing Goals (per-pop + Blended).
# ══════════════════════════════════════════════════════════════

DISP_DATE_ROWS.clear()

brand_results = {}
cv_all = []

for brand_key in RUN_BRANDS:
    cfg = BRAND_CONFIGS[brand_key]
    apply_brand_globals(cfg)
    brand = cfg['brand']
    users_df, revenue_df = load_brand_tables(cfg, as_of_date=AS_OF_DATE)
    print(f'\n[{brand}] loaded users={len(users_df):,} revenue_rows={len(revenue_df):,}')

    u_pop, daily_pop = build_user_revenue_cums(
        users_df.loc[users_df['population'].isin(POPULATIONS)].copy(),
        revenue_df,
        max_day=365,
    )
    cv_pop_df, _curve_pop = build_all_populations(
        u_pop, daily_pop,
        as_of_date=AS_OF_DATE,
        extrapolate_tail=False,
        debug=True,
    )

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
date_df = pd.concat(DISP_DATE_ROWS, ignore_index=True) if DISP_DATE_ROWS else pd.DataFrame()

print('\n' + '=' * 60)
print('DISPERSION DIAGNOSTICS RUN COMPLETE')
print(f'  as_of_date     = {AS_OF_DATE.date()}')
print(f'  experiment     = {EXPERIMENT_TAG}')
print(f'  cv summary rows= {len(cv_df):,}')
print(f'  date detail    = {len(date_df):,}')
print('=' * 60)
'''


DISP_ANALYSIS = r'''# ══════════════════════════════════════════════════════════════
# DISPERSION ANALYSIS — shape of variability (diagnostic only)
# Metrics on AFTER-trim growth_ratios (same as cv_after).
# Do NOT treat MAD/IQR/log values as "pass/fail" vs 15%.
# ══════════════════════════════════════════════════════════════

import matplotlib.pyplot as plt

assert not date_df.empty, 'date_df empty — run the DISPERSION RUN cell first'
assert not cv_df.empty, 'cv_df empty — run the DISPERSION RUN cell first'

NEAR_ZERO_MEDIAN = 1e-9  # absolute; flags invalid median denominator
FOCUS_SET = {(b, p, patch) for b, p, patch in FOCUS_CASES}

# Only observations that remain for cv_after
kept = date_df.loc[~date_df['was_removed_by_existing_trim']].copy()
kept = kept.dropna(subset=['cohort_metric_used_for_cv'])


def _safe_div(num, den):
    if den is None or not np.isfinite(den) or abs(den) <= NEAR_ZERO_MEDIAN:
        return np.nan
    return float(num / den)


def _dispersion_row(g):
    x = g['cohort_metric_used_for_cv'].astype(float).to_numpy()
    x = x[np.isfinite(x)]
    n = int(x.size)
    row = {
        'brand': g['brand'].iloc[0],
        'population': g['population'].iloc[0],
        'patch': g['patch'].iloc[0],
        'n_cohort_dates': n,
        'n_users': int(g['n_users_post_trim'].iloc[0]) if 'n_users_post_trim' in g else None,
        'cv_before': g['cv_before'].iloc[0],
        'cv_after': g['cv_after'].iloc[0],
        'existing_flagged_status': bool(g['flagged'].iloc[0]),
    }
    if n == 0:
        return row

    mean = float(np.mean(x))
    std = float(np.std(x, ddof=0))
    median_x = float(np.median(x))
    mad = float(np.median(np.abs(x - median_x)))
    q10, q25, q75, q90 = np.percentile(x, [10, 25, 75, 90])
    iqr = float(q75 - q25)
    median_ok = abs(median_x) > NEAR_ZERO_MEDIAN
    p10_ok = abs(q10) > NEAR_ZERO_MEDIAN

    pos = x[x > 0]
    pct_pos = float(pos.size / n) if n else 0.0
    if pos.size >= 2:
        log_x = np.log(pos)
        std_log = float(np.std(log_x, ddof=0))
    else:
        std_log = np.nan

    if q10 > 0 and q90 > 0:
        log_p90_p10_spread = float(np.log(q90) - np.log(q10))
        p90_p10_ratio = float(q90 / q10)
        p10_ratio_valid = True
    else:
        log_p90_p10_spread = np.nan
        p90_p10_ratio = np.nan
        p10_ratio_valid = False

    row.update({
        'mean': mean,
        'std': std,
        'median': median_x,
        'MAD': mad,
        'relative_mad_raw': _safe_div(mad, abs(median_x)) if median_ok else np.nan,
        'scaled_mad_cv': _safe_div(1.4826 * mad, abs(median_x)) if median_ok else np.nan,
        'p10': float(q10),
        'p25': float(q25),
        'p75': float(q75),
        'p90': float(q90),
        'IQR': iqr,
        'relative_IQR': _safe_div(iqr, abs(median_x)) if median_ok else np.nan,
        'p90_p10_ratio': p90_p10_ratio,
        'relative_p10_p90_spread': _safe_div(q90 - q10, abs(median_x)) if median_ok else np.nan,
        'p10_ratio_valid': p10_ratio_valid,
        'median_denominator_valid': median_ok,
        'std_log': std_log,
        'log_p90_p10_spread': log_p90_p10_spread,
        'pct_positive_for_log': pct_pos,
        'n_excluded_from_log': int(n - pos.size),
        'skewness': float(pd.Series(x).skew()) if n >= 3 else np.nan,
    })
    return row


master = pd.DataFrame([
    _dispersion_row(g) for _, g in kept.groupby(['brand', 'population', 'patch'], sort=False)
])

# Align flagged from official cv_df if needed
if 'flagged' in cv_df.columns:
    master = master.merge(
        cv_df[['brand', 'population', 'patch', 'flagged']].drop_duplicates(),
        on=['brand', 'population', 'patch'],
        how='left',
        suffixes=('', '_cv'),
    )
    master['existing_flagged_status'] = master['flagged'].fillna(master['existing_flagged_status']).astype(bool)
    master = master.drop(columns=['flagged'], errors='ignore')

master['is_focus_case'] = master.apply(
    lambda r: (r['brand'], r['population'], r['patch']) in FOCUS_SET, axis=1
)

# Within-patch percentile ranks (exploratory; not production thresholds)
rank_cols = {
    'cv_after': 'cv_percentile_within_patch',
    'relative_mad_raw': 'rmad_percentile_within_patch',
    'relative_IQR': 'riqr_percentile_within_patch',
    'relative_p10_p90_spread': 'p10_p90_percentile_within_patch',
    'std_log': 'log_dispersion_percentile_within_patch',
}
for src, dst in rank_cols.items():
    master[dst] = master.groupby('patch')[src].rank(pct=True, method='average')

master['tail_sensitivity_signal'] = (
    master['cv_percentile_within_patch'] - master['riqr_percentile_within_patch']
)
master['cv_minus_rmad_rank'] = (
    master['cv_percentile_within_patch'] - master['rmad_percentile_within_patch']
)
master['cv_minus_log_rank'] = (
    master['cv_percentile_within_patch'] - master['log_dispersion_percentile_within_patch']
)


def _interpret(r):
    """Descriptive only — relative ranks within patch, no 15% pass/fail."""
    cv = r.get('cv_after')
    flagged = bool(r.get('existing_flagged_status'))
    cv_p = r.get('cv_percentile_within_patch')
    rmad_p = r.get('rmad_percentile_within_patch')
    riqr_p = r.get('riqr_percentile_within_patch')
    log_p = r.get('log_dispersion_percentile_within_patch')
    skew = r.get('skewness')
    tail_sig = r.get('tail_sensitivity_signal')

    if cv is None or (isinstance(cv, float) and not np.isfinite(cv)):
        return 'Insufficient data.'

    notes = []
    # absolute high CV (existing flag) vs relative-to-patch
    if flagged and cv_p is not None and cv_p < 0.6:
        notes.append(
            'CV is high in absolute terms but relatively normal compared with other '
            'populations in the same maturity patch.'
        )

    if (tail_sig is not None and np.isfinite(tail_sig) and tail_sig >= 0.25
            and riqr_p is not None and riqr_p <= 0.55):
        notes.append(
            'High CV but relatively concentrated central distribution; tails appear important.'
        )
    elif (riqr_p is not None and rmad_p is not None
          and riqr_p >= 0.7 and rmad_p >= 0.7 and cv_p is not None and cv_p >= 0.7):
        notes.append(
            'High CV and high central dispersion; variability appears broad rather than tail-driven.'
        )
    elif (cv_p is not None and riqr_p is not None and rmad_p is not None
          and cv_p >= 0.7 and riqr_p >= 0.7 and rmad_p >= 0.7):
        notes.append(
            'All dispersion measures agree that this population is unusually volatile.'
        )

    if (skew is not None and np.isfinite(skew) and skew >= 1.0
            and log_p is not None and cv_p is not None
            and (cv_p - log_p) >= 0.2):
        notes.append(
            'Strong right skew; original-scale CV appears more sensitive than log-scale dispersion.'
        )
    elif (log_p is not None and cv_p is not None and (cv_p - log_p) >= 0.25):
        notes.append(
            'Original-scale CV high relative to log-scale dispersion; variability may be multiplicative / asymmetric.'
        )

    if not notes:
        if flagged:
            return 'Mixed evidence; no clear single driver.'
        return 'Distribution appears broadly stable relative to peers (or not in high-CV focus).'
    return ' '.join(notes)


master['diagnostic_interpretation'] = master.apply(_interpret, axis=1)

print('=== MASTER comparison (all brand × population × patch) ===')
master_cols = [
    'brand', 'population', 'patch', 'n_cohort_dates', 'n_users',
    'mean', 'std', 'cv_after', 'median', 'MAD', 'scaled_mad_cv', 'relative_mad_raw',
    'p10', 'p25', 'p75', 'p90', 'IQR', 'relative_IQR',
    'p90_p10_ratio', 'relative_p10_p90_spread',
    'std_log', 'log_p90_p10_spread', 'pct_positive_for_log', 'skewness',
    'existing_flagged_status', 'is_focus_case',
]
print(master[master_cols].sort_values(['patch', 'brand', 'population']).to_string(index=False))

high = master.loc[master['existing_flagged_status']].copy()
print(f'\nFlagged by existing methodology: {len(high)} / {len(master)}')

# ── Disagreement / rank table ──
print('\n=== Within-patch ranks + disagreement signals (all) ===')
rank_view = [
    'brand', 'population', 'patch', 'cv_after',
    'cv_percentile_within_patch', 'rmad_percentile_within_patch',
    'riqr_percentile_within_patch', 'p10_p90_percentile_within_patch',
    'log_dispersion_percentile_within_patch',
    'tail_sensitivity_signal', 'cv_minus_rmad_rank', 'cv_minus_log_rank',
    'existing_flagged_status',
]
print(master[rank_view].sort_values('tail_sensitivity_signal', ascending=False).to_string(index=False))

# ── Focus cases ──
print('\n=== Focus-case inspection ===')
focus = master.loc[master['is_focus_case']].copy()
print(focus[master_cols + ['tail_sensitivity_signal', 'diagnostic_interpretation']].to_string(index=False))

# ── 1->7 dedicated section ──
early = master.loc[master['patch'] == '1->7'].copy()
print('\n=== Dedicated 1->7 section ===')
early_cols = [
    'brand', 'population', 'cv_after', 'relative_mad_raw', 'relative_IQR',
    'p10', 'median', 'p90', 'p90_p10_ratio', 'std_log', 'skewness',
    'cv_percentile_within_patch', 'riqr_percentile_within_patch',
    'tail_sensitivity_signal', 'diagnostic_interpretation',
]
print(early[early_cols].sort_values('cv_after', ascending=False).to_string(index=False))
print(
    '\n1->7 read: if relative_IQR / rmad percentiles stay high with CV, '
    'central majority is also dispersed — not only tails. '
    'If tail_sensitivity_signal is large positive while riqr percentile is mid/low, '
    'CV is more tail-sensitive than the center.'
)

# ── Final high-CV diagnostic table ──
final_cols = [
    'brand', 'population', 'patch',
    'cv_after', 'cv_percentile_within_patch',
    'relative_mad_raw', 'rmad_percentile_within_patch',
    'relative_IQR', 'riqr_percentile_within_patch',
    'p10', 'median', 'p90', 'p90_p10_ratio', 'relative_p10_p90_spread',
    'std_log', 'log_dispersion_percentile_within_patch',
    'skewness', 'tail_sensitivity_signal', 'diagnostic_interpretation',
]
final = high[final_cols].sort_values('cv_after', ascending=False).copy() if not high.empty else master.loc[master['is_focus_case'], final_cols].copy()
print('\n=== FINAL diagnostic table (flagged / high-CV) ===')
print(final.to_string(index=False))

# ── Visualizations: distribution strips for flagged + focus ──
interesting = master.loc[master['existing_flagged_status'] | master['is_focus_case']].copy()
keys = list(zip(interesting['brand'], interesting['population'], interesting['patch']))

def _overlay_strip(ax, vals, title):
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        ax.set_title(title + ' (empty)')
        return
    y = np.zeros_like(vals)
    ax.scatter(vals, y, alpha=0.55, s=28)
    for q, name, ls in [
        (np.percentile(vals, 10), 'P10', ':'),
        (np.percentile(vals, 25), 'P25', '--'),
        (np.median(vals), 'Median', '-'),
        (np.percentile(vals, 75), 'P75', '--'),
        (np.percentile(vals, 90), 'P90', ':'),
        (np.mean(vals), 'Mean', '-.'),
    ]:
        ax.axvline(q, linestyle=ls, linewidth=1.2, label=f'{name}={q:.3f}')
    ax.set_yticks([])
    ax.set_title(title)
    ax.legend(fontsize=7, loc='upper right')


n_plots = len(keys)
if n_plots:
    ncols = 2
    nrows = int(np.ceil(n_plots / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 2.6 * nrows), squeeze=False)
    for i, (b, p, patch) in enumerate(keys):
        ax = axes[i // ncols][i % ncols]
        sub = kept.loc[
            (kept['brand'] == b) & (kept['population'] == p) & (kept['patch'] == patch),
            'cohort_metric_used_for_cv',
        ]
        _overlay_strip(ax, sub.values, f'{b} | {p} | {patch}')
    for j in range(n_plots, nrows * ncols):
        axes[j // ncols][j % ncols].axis('off')
    fig.suptitle('After-trim growth_ratio — flagged + focus (P10/P25/Med/P75/P90/Mean)', y=1.01)
    plt.tight_layout()
    plt.show()

# Normalized by median
if n_plots:
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 2.6 * nrows), squeeze=False)
    for i, (b, p, patch) in enumerate(keys):
        ax = axes[i // ncols][i % ncols]
        sub = kept.loc[
            (kept['brand'] == b) & (kept['population'] == p) & (kept['patch'] == patch),
            'cohort_metric_used_for_cv',
        ].astype(float)
        med = np.nanmedian(sub.values)
        if med is None or not np.isfinite(med) or abs(med) <= NEAR_ZERO_MEDIAN:
            ax.set_title(f'{b} | {p} | {patch} (median invalid)')
            continue
        _overlay_strip(ax, (sub / med).values, f'{b} | {p} | {patch}  (x / median)')
    for j in range(n_plots, nrows * ncols):
        axes[j // ncols][j % ncols].axis('off')
    fig.suptitle('Normalized growth_ratio (÷ median) — shape compare', y=1.01)
    plt.tight_layout()
    plt.show()

# Combined 1->7 normalized
early_kept = kept.loc[kept['patch'] == '1->7'].copy()
if not early_kept.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    for (b, p), g in early_kept.groupby(['brand', 'population']):
        x = g['cohort_metric_used_for_cv'].astype(float).to_numpy()
        med = np.nanmedian(x)
        if not np.isfinite(med) or abs(med) <= NEAR_ZERO_MEDIAN:
            continue
        xn = x / med
        ax.scatter(xn, np.full_like(xn, 0.0), alpha=0.35, s=22, label=f'{b}/{p}')
    ax.axvline(1.0, color='black', linewidth=1)
    ax.set_yticks([])
    ax.set_xlabel('growth_ratio / median')
    ax.set_title('All 1->7 populations — normalized overlay')
    ax.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.show()

# Scatter: CV vs robust measures
scatter_pairs = [
    ('relative_mad_raw', 'CV vs relative_mad_raw'),
    ('relative_IQR', 'CV vs relative_IQR'),
    ('relative_p10_p90_spread', 'CV vs relative P10–P90 spread'),
    ('std_log', 'CV vs std_log'),
]
fig, axes = plt.subplots(2, 2, figsize=(11, 9))
for ax, (col, title) in zip(axes.ravel(), scatter_pairs):
    m = master.dropna(subset=['cv_after', col])
    ax.scatter(m[col], m['cv_after'], alpha=0.55, s=30, c='steelblue', label='all')
    f = m.loc[m['existing_flagged_status']]
    if not f.empty:
        ax.scatter(f[col], f['cv_after'], s=55, facecolors='none', edgecolors='crimson',
                   linewidths=1.5, label='flagged')
    ax.set_xlabel(col)
    ax.set_ylabel('cv_after')
    ax.set_title(title)
    ax.legend(fontsize=7)
plt.tight_layout()
plt.show()

print('\\n=== Brief answers (fill after reading tables/plots; edit as needed) ===')
_q = [
    '1. When CV is high, do MAD/IQR/P10-P90 generally confirm broad dispersion?',
    '   -> See flagged rows: compare cv_percentile vs riqr/rmad percentiles.',
    '2. Which high-CV cases appear primarily tail-driven?',
    '   -> Large positive tail_sensitivity_signal + lower riqr percentile.',
    '3. Which stay highly dispersed in the central distribution?',
    '   -> High cv + high riqr + high rmad percentiles together.',
    '4. Is 1->7 broadly dispersed centrally, or mainly tails?',
    '   -> See dedicated 1->7 section + normalized overlay.',
    '5. Does log-scale change interpretation?',
    '   -> Large cv_minus_log_rank; strong skew notes.',
    '6. Cases where CV looks high but robust center looks normal for the patch?',
    '   -> High tail_sensitivity_signal / cv_minus_rmad_rank.',
    '7. What does CV appear to measure in problematic cases?',
    '   -> Descriptive only from patterns above — do NOT recommend replacing CV here.',
]
print('\\n'.join(_q))
print(
    'Reminder: relative_mad_raw / relative_IQR are NOT on the same scale as CV=0.15. '
    'This notebook does not change Marketing Goals methodology.'
)
'''


DISP_EXPORT = r'''# ══════════════════════════════════════════════════════════════
# EXPORT — dispersion CSVs only (does not overwrite other experiments)
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

local_paths = {
    'cv_summary': f'combined_cv_summary_{run_tag}_dispersion.csv',
    'master': f'dispersion_master_{run_tag}.csv',
    'final': f'dispersion_final_high_cv_{run_tag}.csv',
    'dates': f'dispersion_cohort_dates_{run_tag}.csv',
}
cv_df.to_csv(local_paths['cv_summary'], index=False)
master.to_csv(local_paths['master'], index=False)
final.to_csv(local_paths['final'], index=False)
date_df.to_csv(local_paths['dates'], index=False)

print('Run tag:', run_tag)
print('Saved in working directory:')
for p in local_paths.values():
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
    cv_df.to_csv(out_dir / 'combined_cv_summary_dispersion.csv', index=False)
    master.to_csv(out_dir / 'dispersion_master.csv', index=False)
    final.to_csv(out_dir / 'dispersion_final_high_cv.csv', index=False)
    date_df.to_csv(out_dir / 'dispersion_cohort_dates.csv', index=False)
    meta = pd.DataFrame([{
        'run_tag': run_tag,
        'as_of_date': str(AS_OF_DATE.date()),
        'brands': ','.join(RUN_BRANDS),
        'brand_slug': brand_slug,
        'run_ts': run_ts,
        'exported_at': exported_at.isoformat(timespec='seconds'),
        'env': 'colab',
        'experiment_tag': EXPERIMENT_TAG,
        'purpose': 'dispersion_diagnostics_only',
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

    set_src(nb, 0, TITLE_MD)

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
EXPERIMENT_TAG = 'dispersion_diagnostics'  # ADDED: distinct runs/ folder

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
    assert "'cv_threshold': 0.175" in s4
    set_src(nb, 4, s4)

    # Instrument patch_cv (keep production CV math)
    s8 = get_src(nb, 8)
    assert "def patch_cv_adaptive(" in s8
    assert "DISP_DATE_ROWS" not in s8
    s8 = s8.replace(
        "# ══════════════════════════════════════════════════════════════\n"
        "# ADAPTIVE CV ANALYSIS — persistent trim\n"
        "# ══════════════════════════════════════════════════════════════\n\n",
        INSTRUMENT_HEADER,
        1,
    )
    s8 = s8.replace(
        "    return patch, stats, removed, flagged, newly_excluded\n",
        INSTRUMENT_BEFORE_RETURN + "    return patch, stats, removed, flagged, newly_excluded\n",
        1,
    )
    s8 = s8.replace(
        "print('Adaptive CV function defined (persistent trim).')",
        "print('Adaptive CV function defined (persistent trim + dispersion instrumentation).')",
    )
    set_src(nb, 8, s8)

    set_src(
        nb,
        10,
        "# ADDED: organic helper skipped in dispersion_diagnostics.\n"
        "print('Organic helpers skipped (dispersion_diagnostics).')\n",
    )
    set_src(nb, 12, DISP_RUN)
    set_src(nb, 13, DISP_ANALYSIS)
    set_src(nb, 14, DISP_EXPORT)
    if len(nb["cells"]) > 15:
        set_src(nb, 15, "# (unused in dispersion_diagnostics)\npass\n")

    for c in nb["cells"]:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1))

    src = "\n".join(get_src(nb, i) for i in range(len(nb["cells"])))
    checks = {
        "AS_OF": "2026-08-03" in src,
        "tag": "dispersion_diagnostics" in src,
        "LS 0.175 kept": "'cv_threshold': 0.175" in src,
        "no winsor ladder": "WINSOR_ESCALATION" not in src,
        "instrument": "DISP_DATE_ROWS" in src,
        "relative_mad_raw": "relative_mad_raw" in src,
        "relative_IQR": "relative_IQR" in src,
        "std_log": "std_log" in src,
        "ranks": "cv_percentile_within_patch" in src,
        "tail signal": "tail_sensitivity_signal" in src,
        "focus": "FOCUS_CASES" in src,
        "final": "diagnostic_interpretation" in src,
        "filename": OUT_NB.name == "marketing_goals_dispersion_diagnostics.ipynb",
        "no oos walkforward": "walk_forward" not in src.lower() or "DISPERSION" in src,
    }
    for k, ok in checks.items():
        print(("OK" if ok else "FAIL"), k)
    assert all(checks.values())
    print("Wrote", OUT_NB)


if __name__ == "__main__":
    main()
