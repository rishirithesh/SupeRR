import pandas as pd
import numpy as np

import balanced_pressure as bp

bbb = bp.bbb

# Ensure legal deliveries, batsman runs, bowler runs, wickets
bbb['is_hp'] = (bbb['pressure_index'] >= 65).astype(int)

# Filter to legal balls for ball counts and strike rates
legal_bbb = bbb[bbb['is_legal'] == 1].copy()

# Add boundary indicator
legal_bbb['is_boundary'] = (legal_bbb['is_four'] | legal_bbb['is_six']).astype(int)
legal_bbb['is_dot'] = (legal_bbb['runs'] == 0).astype(int)

print(f'Total legal deliveries: {len(legal_bbb)}')
hp_sum = legal_bbb['is_hp'].sum()
hp_pct = legal_bbb['is_hp'].mean() * 100
print(f'High pressure legal deliveries: {hp_sum} ({hp_pct:.1f}%)')

# ==========================================
# 1. BATTER EVALUATION
# ==========================================
# Group by striker_id and striker_name
def evaluate_batters(min_hp_balls=60, min_total_balls=150):
    # Overall / Baseline stats
    all_bat = legal_bbb.groupby(['striker_id', 'striker_name']).agg(
        total_balls=('runs', 'count'),
        total_runs=('runs', 'sum'),
        total_dismissals=('is_wicket', 'sum'),
        total_fours=('is_four', 'sum'),
        total_sixes=('is_six', 'sum'),
        total_dots=('is_dot', 'sum')
    ).reset_index()
    all_bat['overall_sr'] = (all_bat['total_runs'] / all_bat['total_balls']) * 100.0
    all_bat['overall_avg'] = all_bat['total_runs'] / np.maximum(1, all_bat['total_dismissals'])

    # High pressure stats
    hp_bat = legal_bbb[legal_bbb['is_hp'] == 1].groupby(['striker_id', 'striker_name']).agg(
        hp_balls=('runs', 'count'),
        hp_runs=('runs', 'sum'),
        hp_dismissals=('is_wicket', 'sum'),
        hp_fours=('is_four', 'sum'),
        hp_sixes=('is_six', 'sum'),
        hp_dots=('is_dot', 'sum')
    ).reset_index()
    hp_bat['hp_sr'] = (hp_bat['hp_runs'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_avg'] = hp_bat['hp_runs'] / np.maximum(1, hp_bat['hp_dismissals'])
    hp_bat['hp_dot_pct'] = (hp_bat['hp_dots'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_boundary_pct'] = ((hp_bat['hp_fours'] + hp_bat['hp_sixes']) / hp_bat['hp_balls']) * 100.0

    # Low/Medium pressure baseline stats (is_hp == 0)
    lp_bat = legal_bbb[legal_bbb['is_hp'] == 0].groupby(['striker_id', 'striker_name']).agg(
        lp_balls=('runs', 'count'),
        lp_runs=('runs', 'sum'),
        lp_dismissals=('is_wicket', 'sum')
    ).reset_index()
    lp_bat['lp_sr'] = (lp_bat['lp_runs'] / lp_bat['lp_balls']) * 100.0
    lp_bat['lp_avg'] = lp_bat['lp_runs'] / np.maximum(1, lp_bat['lp_dismissals'])

    # Merge
    merged = hp_bat.merge(lp_bat, on=['striker_id', 'striker_name'], how='inner')
    merged = merged.merge(all_bat[['striker_id', 'total_balls', 'total_runs', 'overall_sr', 'overall_avg']], on='striker_id', how='left')

    # Filter sample size
    filtered = merged[(merged['hp_balls'] >= min_hp_balls) & (merged['total_balls'] >= min_total_balls)].copy()

    # Prior means for Empirical Bayes shrinkage
    pop_hp_sr = (filtered['hp_runs'].sum() / filtered['hp_balls'].sum()) * 100.0
    pop_hp_avg = filtered['hp_runs'].sum() / np.maximum(1, filtered['hp_dismissals'].sum())

    # Bayesian shrinkage (K=50 balls)
    K = 50.0
    filtered['shrunk_hp_sr'] = (filtered['hp_balls'] * filtered['hp_sr'] + K * pop_hp_sr) / (filtered['hp_balls'] + K)
    filtered['shrunk_hp_avg'] = (filtered['hp_balls'] * filtered['hp_avg'] + K * pop_hp_avg) / (filtered['hp_balls'] + K)

    # Clutch Differentials
    filtered['sr_delta'] = filtered['hp_sr'] - filtered['lp_sr']
    filtered['sr_ratio'] = filtered['hp_sr'] / np.maximum(100.0, filtered['lp_sr'])
    filtered['avg_ratio'] = filtered['hp_avg'] / np.maximum(15.0, filtered['lp_avg'])

    # Comprehensive Pressure Score (Batting)
    # Balances:
    # 1. Shrunk High Pressure SR (normalized to mean 100)
    # 2. Shrunk High Pressure Average (normalized to mean 100)
    # 3. Clutch SR Delta (bonus for striking faster under pressure)
    # 4. Low Dot % & High Boundary % under pressure
    # 5. Volume confidence multiplier: log(hp_balls)
    norm_sr = (filtered['shrunk_hp_sr'] - pop_hp_sr) / filtered['shrunk_hp_sr'].std()
    norm_avg = (filtered['shrunk_hp_avg'] - pop_hp_avg) / filtered['shrunk_hp_avg'].std()
    norm_delta = (filtered['sr_delta'] - filtered['sr_delta'].mean()) / filtered['sr_delta'].std()
    norm_bound = (filtered['hp_boundary_pct'] - filtered['hp_boundary_pct'].mean()) / filtered['hp_boundary_pct'].std()
    norm_dot = -(filtered['hp_dot_pct'] - filtered['hp_dot_pct'].mean()) / filtered['hp_dot_pct'].std()

    # Composite Batting Pressure Index (BPI)
    filtered['bpi_score'] = (
        0.35 * norm_sr +
        0.25 * norm_avg +
        0.20 * norm_delta +
        0.10 * norm_bound +
        0.10 * norm_dot
    )

    return filtered.sort_values('bpi_score', ascending=False)

batters = evaluate_batters(min_hp_balls=60, min_total_balls=180)
print('\n=== TOP 20 BATTERS UNDER PRESSURE ===')
print(batters[['striker_name', 'hp_balls', 'hp_runs', 'hp_sr', 'lp_sr', 'sr_delta', 'hp_avg', 'lp_avg', 'hp_boundary_pct', 'bpi_score']].head(20).to_string(index=False))
