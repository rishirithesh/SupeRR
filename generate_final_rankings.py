import pandas as pd
import numpy as np

import test_tiers as tt

legal_bbb = tt.legal_bbb

# ==========================================
# 1. TIER-WEIGHTED BATTER EVALUATION
# ==========================================
def get_ranked_batters(min_hp_balls=80, min_total_balls=200):
    # Overall
    all_bat = legal_bbb.groupby(['striker_id', 'striker_name']).agg(
        total_matches=('match_id', 'nunique'),
        total_balls=('runs', 'count'),
        total_runs=('runs', 'sum'),
        total_dismissals=('is_wicket', 'sum'),
        total_rae_w=('bat_rae_w', 'sum'),
        ipl_balls=('is_ipl', 'sum')
    ).reset_index()
    all_bat['overall_sr'] = (all_bat['total_runs'] / all_bat['total_balls']) * 100.0
    all_bat['overall_avg'] = all_bat['total_runs'] / np.maximum(1, all_bat['total_dismissals'])

    # High pressure
    hp_bat = legal_bbb[legal_bbb['is_hp'] == 1].groupby(['striker_id', 'striker_name']).agg(
        hp_matches=('match_id', 'nunique'),
        hp_balls=('runs', 'count'),
        hp_runs=('runs', 'sum'),
        hp_dismissals=('is_wicket', 'sum'),
        hp_fours=('is_four', 'sum'),
        hp_sixes=('is_six', 'sum'),
        hp_dots=('is_dot', 'sum'),
        hp_rae_w=('bat_rae_w', 'sum'),
        hp_ipl_balls=('is_ipl', 'sum')
    ).reset_index()
    hp_bat['hp_sr'] = (hp_bat['hp_runs'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_avg'] = hp_bat['hp_runs'] / np.maximum(1, hp_bat['hp_dismissals'])
    hp_bat['hp_boundary_pct'] = ((hp_bat['hp_fours'] + hp_bat['hp_sixes']) / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_dot_pct'] = (hp_bat['hp_dots'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_rae100_w'] = (hp_bat['hp_rae_w'] / hp_bat['hp_balls']) * 100.0

    # Low/Medium pressure baseline
    lp_bat = legal_bbb[legal_bbb['is_hp'] == 0].groupby('striker_id').agg(
        lp_balls=('runs', 'count'),
        lp_runs=('runs', 'sum'),
        lp_dismissals=('is_wicket', 'sum'),
        lp_rae_w=('bat_rae_w', 'sum')
    ).reset_index()
    lp_bat['lp_sr'] = (lp_bat['lp_runs'] / lp_bat['lp_balls']) * 100.0
    lp_bat['lp_avg'] = lp_bat['lp_runs'] / np.maximum(1, lp_bat['lp_dismissals'])
    lp_bat['lp_rae100_w'] = (lp_bat['lp_rae_w'] / lp_bat['lp_balls']) * 100.0

    # Merge
    merged = hp_bat.merge(lp_bat, on='striker_id', how='inner')
    merged = merged.merge(all_bat[['striker_id', 'total_matches', 'total_balls', 'total_runs', 'overall_sr', 'overall_avg', 'ipl_balls']], on='striker_id', how='left')

    # Filter sample size
    df = merged[(merged['hp_balls'] >= min_hp_balls) & (merged['total_balls'] >= min_total_balls)].copy()

    # Empirical Bayes Shrinkage
    K = 60.0
    pop_sr = (df['hp_runs'].sum() / df['hp_balls'].sum()) * 100.0
    pop_avg = df['hp_runs'].sum() / np.maximum(1, df['hp_dismissals'].sum())
    pop_rae = (df['hp_rae_w'].sum() / df['hp_balls'].sum()) * 100.0

    df['reg_hp_sr'] = (df['hp_balls'] * df['hp_sr'] + K * pop_sr) / (df['hp_balls'] + K)
    df['reg_hp_avg'] = (df['hp_balls'] * df['hp_avg'] + K * pop_avg) / (df['hp_balls'] + K)
    df['reg_hp_rae100_w'] = (df['hp_balls'] * df['hp_rae100_w'] + K * pop_rae) / (df['hp_balls'] + K)

    # Clutch Differentials
    df['clutch_sr_delta'] = df['hp_sr'] - df['lp_sr']
    df['clutch_rae_delta'] = df['hp_rae100_w'] - df['lp_rae100_w']
    df['clutch_avg_ratio'] = df['hp_avg'] / np.maximum(15.0, df['lp_avg'])

    # Standardized Features
    z_rae = (df['reg_hp_rae100_w'] - df['reg_hp_rae100_w'].mean()) / df['reg_hp_rae100_w'].std()
    z_avg = (df['reg_hp_avg'] - df['reg_hp_avg'].mean()) / df['reg_hp_avg'].std()
    z_clutch = (df['clutch_rae_delta'] - df['clutch_rae_delta'].mean()) / df['clutch_rae_delta'].std()
    z_bound = (df['hp_boundary_pct'] - df['hp_boundary_pct'].mean()) / df['hp_boundary_pct'].std()
    z_dot = -(df['hp_dot_pct'] - df['hp_dot_pct'].mean()) / df['hp_dot_pct'].std()

    # Sample credibility factor
    sample_factor = np.clip(np.sqrt(df['hp_balls']) / np.sqrt(300), 0.85, 1.15)

    raw_score = (
        0.35 * z_rae +
        0.25 * z_clutch +
        0.20 * z_avg +
        0.10 * z_bound +
        0.10 * z_dot
    )

    df['rating'] = 50.0 + 15.0 * (raw_score * sample_factor - (raw_score * sample_factor).mean()) / (raw_score * sample_factor).std()
    return df.sort_values('rating', ascending=False)

# ==========================================
# 2. TIER-WEIGHTED BOWLER EVALUATION
# ==========================================
def get_ranked_bowlers(min_hp_balls=90, min_total_balls=240):
    all_bowl = legal_bbb.groupby(['bowler_id', 'bowler_name']).agg(
        total_matches=('match_id', 'nunique'),
        total_balls=('is_legal', 'count'),
        total_runs=('bowler_runs', 'sum'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_rsae_w=('bowl_rsae_w', 'sum'),
        ipl_balls=('is_ipl', 'sum')
    ).reset_index()
    all_bowl['overall_econ'] = all_bowl['total_runs'] / (all_bowl['total_balls'] / 6.0)
    all_bowl['overall_sr'] = all_bowl['total_balls'] / np.maximum(1, all_bowl['total_wickets'])

    # High pressure
    hp_bowl = legal_bbb[legal_bbb['is_hp'] == 1].groupby(['bowler_id', 'bowler_name']).agg(
        hp_matches=('match_id', 'nunique'),
        hp_balls=('is_legal', 'count'),
        hp_runs=('bowler_runs', 'sum'),
        hp_wickets=('is_bowler_wicket', 'sum'),
        hp_dots=('is_bowler_dot', 'sum'),
        hp_boundaries=('is_bowler_boundary', 'sum'),
        hp_rsae_w=('bowl_rsae_w', 'sum'),
        hp_wae_w=('bowl_wae_w', 'sum'),
        hp_ipl_balls=('is_ipl', 'sum')
    ).reset_index()
    hp_bowl['hp_econ'] = hp_bowl['hp_runs'] / (hp_bowl['hp_balls'] / 6.0)
    hp_bowl['hp_sr'] = hp_bowl['hp_balls'] / np.maximum(1, hp_bowl['hp_wickets'])
    hp_bowl['hp_dot_pct'] = (hp_bowl['hp_dots'] / hp_bowl['hp_balls']) * 100.0
    hp_bowl['hp_boundary_pct'] = (hp_bowl['hp_boundaries'] / hp_bowl['hp_balls']) * 100.0
    hp_bowl['hp_rsae6_w'] = (hp_bowl['hp_rsae_w'] / (hp_bowl['hp_balls'] / 6.0))

    # Low/Medium pressure baseline
    lp_bowl = legal_bbb[legal_bbb['is_hp'] == 0].groupby('bowler_id').agg(
        lp_balls=('is_legal', 'count'),
        lp_runs=('bowler_runs', 'sum'),
        lp_wickets=('is_bowler_wicket', 'sum'),
        lp_rsae_w=('bowl_rsae_w', 'sum')
    ).reset_index()
    lp_bowl['lp_econ'] = lp_bowl['lp_runs'] / (lp_bowl['lp_balls'] / 6.0)
    lp_bowl['lp_sr'] = lp_bowl['lp_balls'] / np.maximum(1, lp_bowl['lp_wickets'])
    lp_bowl['lp_rsae6_w'] = (lp_bowl['lp_rsae_w'] / (lp_bowl['lp_balls'] / 6.0))

    # Merge
    merged = hp_bowl.merge(lp_bowl, on='bowler_id', how='inner')
    merged = merged.merge(all_bowl[['bowler_id', 'total_matches', 'total_balls', 'total_runs', 'overall_econ', 'overall_sr', 'ipl_balls']], on='bowler_id', how='left')

    df = merged[(merged['hp_balls'] >= min_hp_balls) & (merged['total_balls'] >= min_total_balls)].copy()

    # Shrinkage
    K = 60.0
    pop_econ = df['hp_runs'].sum() / (df['hp_balls'].sum() / 6.0)
    pop_sr = df['hp_balls'].sum() / np.maximum(1, df['hp_wickets'].sum())
    pop_rsae6 = df['hp_rsae_w'].sum() / (df['hp_balls'].sum() / 6.0)

    df['reg_hp_econ'] = (df['hp_balls'] * df['hp_econ'] + K * pop_econ) / (df['hp_balls'] + K)
    df['reg_hp_sr'] = (df['hp_balls'] * df['hp_sr'] + K * pop_sr) / (df['hp_balls'] + K)
    df['reg_hp_rsae6_w'] = (df['hp_balls'] * df['hp_rsae6_w'] + K * pop_rsae6) / (df['hp_balls'] + K)

    # Clutch Differentials
    df['clutch_rsae_delta'] = df['hp_rsae6_w'] - df['lp_rsae6_w']
    df['clutch_sr_delta'] = df['lp_sr'] - df['hp_sr']

    # Standardized Features
    z_rsae = (df['reg_hp_rsae6_w'] - df['reg_hp_rsae6_w'].mean()) / df['reg_hp_rsae6_w'].std()
    z_sr = -(df['reg_hp_sr'] - df['reg_hp_sr'].mean()) / df['reg_hp_sr'].std()
    z_clutch = (df['clutch_rsae_delta'] - df['clutch_rsae_delta'].mean()) / df['clutch_rsae_delta'].std()
    z_dot = (df['hp_dot_pct'] - df['hp_dot_pct'].mean()) / df['hp_dot_pct'].std()
    z_bound = -(df['hp_boundary_pct'] - df['hp_boundary_pct'].mean()) / df['hp_boundary_pct'].std()

    sample_factor = np.clip(np.sqrt(df['hp_balls']) / np.sqrt(300), 0.85, 1.15)

    raw_score = (
        0.35 * z_rsae +
        0.25 * z_sr +
        0.20 * z_clutch +
        0.10 * z_dot +
        0.10 * z_bound
    )

    df['rating'] = 50.0 + 15.0 * (raw_score * sample_factor - (raw_score * sample_factor).mean()) / (raw_score * sample_factor).std()
    return df.sort_values('rating', ascending=False)

b = get_ranked_batters(min_hp_balls=80, min_total_balls=200)
bw = get_ranked_bowlers(min_hp_balls=90, min_total_balls=240)

print('\n' + '='*85)
print('FINAL TOP 12 BATTERS UNDER PRESSURE')
print('='*85)
b_cols = ['striker_name', 'hp_balls', 'hp_runs', 'hp_sr', 'lp_sr', 'clutch_sr_delta', 'hp_avg', 'hp_boundary_pct', 'hp_dot_pct', 'rating']
print(b[b_cols].head(12).to_string(index=False))

print('\n' + '='*85)
print('FINAL TOP 12 BOWLERS UNDER PRESSURE')
print('='*85)
bw_cols = ['bowler_name', 'hp_balls', 'hp_wickets', 'hp_econ', 'lp_econ', 'hp_rsae6_w', 'hp_sr', 'hp_dot_pct', 'rating']
print(bw[bw_cols].head(12).to_string(index=False))

