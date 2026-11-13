import pandas as pd
import numpy as np

import balanced_pressure as bp

bbb = bp.bbb
bbb['is_hp'] = (bbb['pressure_index'] >= 65).astype(int)
bbb['is_ipl'] = bbb['comp_name'].str.contains('IPL', case=False, na=False).astype(int)

# Legal deliveries
legal_bbb = bbb[bbb['is_legal'] == 1].copy()
legal_bbb['is_boundary'] = (legal_bbb['is_four'] | legal_bbb['is_six']).astype(int)
legal_bbb['is_dot'] = (legal_bbb['runs'] == 0).astype(int)
legal_bbb['is_bowler_dot'] = (legal_bbb['bowler_runs'] == 0).astype(int)
legal_bbb['is_bowler_boundary'] = (legal_bbb['runs'] >= 4).astype(int)

# 1. Compute Context Expectations (by is_ipl and is_hp)
context_stats = legal_bbb.groupby(['is_ipl', 'is_hp']).agg(
    exp_bat_runs=('runs', 'mean'),
    exp_bat_wkt=('is_wicket', 'mean'),
    exp_bowl_runs=('bowler_runs', 'mean'),
    exp_bowl_wkt=('is_bowler_wicket', 'mean')
).reset_index()

legal_bbb = legal_bbb.merge(context_stats, on=['is_ipl', 'is_hp'], how='left')

# Delivery-level residuals
legal_bbb['bat_rae'] = legal_bbb['runs'] - legal_bbb['exp_bat_runs']
legal_bbb['bat_wae'] = legal_bbb['exp_bat_wkt'] - legal_bbb['is_wicket']  # positive = avoided dismissal
legal_bbb['bowl_rsae'] = legal_bbb['exp_bowl_runs'] - legal_bbb['bowler_runs']  # positive = runs saved
legal_bbb['bowl_wae'] = legal_bbb['is_bowler_wicket'] - legal_bbb['exp_bowl_wkt']  # positive = wickets gained

print('Computed delivery-level context residuals.')

# ==========================================
# 2. BATTER EVALUATION MODEL
# ==========================================
def rank_batters(min_hp_balls=80, min_total_balls=200):
    # Aggregation across all legal balls
    all_bat = legal_bbb.groupby(['striker_id', 'striker_name']).agg(
        total_matches=('match_id', 'nunique'),
        total_balls=('runs', 'count'),
        total_runs=('runs', 'sum'),
        total_dismissals=('is_wicket', 'sum'),
        total_fours=('is_four', 'sum'),
        total_sixes=('is_six', 'sum'),
        total_dots=('is_dot', 'sum'),
        total_rae=('bat_rae', 'sum')
    ).reset_index()
    all_bat['overall_sr'] = (all_bat['total_runs'] / all_bat['total_balls']) * 100.0
    all_bat['overall_avg'] = all_bat['total_runs'] / np.maximum(1, all_bat['total_dismissals'])
    all_bat['overall_rae100'] = (all_bat['total_rae'] / all_bat['total_balls']) * 100.0

    # High pressure aggregation
    hp_bat = legal_bbb[legal_bbb['is_hp'] == 1].groupby(['striker_id', 'striker_name']).agg(
        hp_matches=('match_id', 'nunique'),
        hp_balls=('runs', 'count'),
        hp_runs=('runs', 'sum'),
        hp_dismissals=('is_wicket', 'sum'),
        hp_fours=('is_four', 'sum'),
        hp_sixes=('is_six', 'sum'),
        hp_dots=('is_dot', 'sum'),
        hp_rae=('bat_rae', 'sum'),
        hp_wae=('bat_wae', 'sum'),
        hp_ipl_balls=('is_ipl', 'sum')
    ).reset_index()
    hp_bat['hp_sr'] = (hp_bat['hp_runs'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_avg'] = hp_bat['hp_runs'] / np.maximum(1, hp_bat['hp_dismissals'])
    hp_bat['hp_boundary_pct'] = ((hp_bat['hp_fours'] + hp_bat['hp_sixes']) / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_dot_pct'] = (hp_bat['hp_dots'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_rae100'] = (hp_bat['hp_rae'] / hp_bat['hp_balls']) * 100.0
    hp_bat['hp_ipl_share'] = hp_bat['hp_ipl_balls'] / hp_bat['hp_balls']

    # Non-HP baseline
    lp_bat = legal_bbb[legal_bbb['is_hp'] == 0].groupby('striker_id').agg(
        lp_balls=('runs', 'count'),
        lp_runs=('runs', 'sum'),
        lp_dismissals=('is_wicket', 'sum'),
        lp_rae=('bat_rae', 'sum')
    ).reset_index()
    lp_bat['lp_sr'] = (lp_bat['lp_runs'] / lp_bat['lp_balls']) * 100.0
    lp_bat['lp_avg'] = lp_bat['lp_runs'] / np.maximum(1, lp_bat['lp_dismissals'])
    lp_bat['lp_rae100'] = (lp_bat['lp_rae'] / lp_bat['lp_balls']) * 100.0

    # Merge
    merged = hp_bat.merge(lp_bat, on='striker_id', how='inner')
    merged = merged.merge(all_bat[['striker_id', 'total_matches', 'total_balls', 'total_runs', 'overall_sr', 'overall_avg', 'overall_rae100']], on='striker_id', how='left')

    # Filter sample size
    df = merged[(merged['hp_balls'] >= min_hp_balls) & (merged['total_balls'] >= min_total_balls)].copy()

    # Empirical Bayes Shrinkage for HP Strike Rate and RAE100
    # Prior weight K_b = 60 balls
    K_b = 60.0
    pop_sr = (df['hp_runs'].sum() / df['hp_balls'].sum()) * 100.0
    pop_avg = df['hp_runs'].sum() / np.maximum(1, df['hp_dismissals'].sum())
    pop_rae100 = (df['hp_rae'].sum() / df['hp_balls'].sum()) * 100.0

    df['reg_hp_sr'] = (df['hp_balls'] * df['hp_sr'] + K_b * pop_sr) / (df['hp_balls'] + K_b)
    df['reg_hp_avg'] = (df['hp_balls'] * df['hp_avg'] + K_b * pop_avg) / (df['hp_balls'] + K_b)
    df['reg_hp_rae100'] = (df['hp_balls'] * df['hp_rae100'] + K_b * pop_rae100) / (df['hp_balls'] + K_b)

    # Clutch Differential: Performance under pressure vs player's own baseline
    df['clutch_sr_delta'] = df['hp_sr'] - df['lp_sr']
    df['clutch_rae_delta'] = df['hp_rae100'] - df['lp_rae100']
    df['clutch_avg_ratio'] = df['hp_avg'] / np.maximum(15.0, df['lp_avg'])

    # Standardized Features
    z_rae = (df['reg_hp_rae100'] - df['reg_hp_rae100'].mean()) / df['reg_hp_rae100'].std()
    z_avg = (df['reg_hp_avg'] - df['reg_hp_avg'].mean()) / df['reg_hp_avg'].std()
    z_clutch = (df['clutch_rae_delta'] - df['clutch_rae_delta'].mean()) / df['clutch_rae_delta'].std()
    z_bound = (df['hp_boundary_pct'] - df['hp_boundary_pct'].mean()) / df['hp_boundary_pct'].std()
    z_dot = -(df['hp_dot_pct'] - df['hp_dot_pct'].mean()) / df['hp_dot_pct'].std()

    # Reliability & Sample Weighting factor: sqrt(hp_balls) confidence
    # Sample confidence factor scales from 0.85 to 1.05
    sample_factor = np.clip(np.sqrt(df['hp_balls']) / np.sqrt(300), 0.85, 1.15)

    # Composite Pressure Batting Rating (PBR)
    # 35% Pressure Runs Above Expectation (Context adjusted)
    # 25% Clutch Delta (Elevation over own baseline)
    # 20% Dismissal Resistance / Pressure Average
    # 10% Boundary Execution
    # 10% Dot Ball Minimization
    raw_score = (
        0.35 * z_rae +
        0.25 * z_clutch +
        0.20 * z_avg +
        0.10 * z_bound +
        0.10 * z_dot
    )

    df['final_pbr'] = raw_score * sample_factor
    # Scale to 100-based index for easy interpretation
    df['pressure_batting_rating'] = 50.0 + 15.0 * (df['final_pbr'] - df['final_pbr'].mean()) / df['final_pbr'].std()

    return df.sort_values('pressure_batting_rating', ascending=False)

# ==========================================
# 3. BOWLER EVALUATION MODEL
# ==========================================
def rank_bowlers(min_hp_balls=90, min_total_balls=240):
    all_bowl = legal_bbb.groupby(['bowler_id', 'bowler_name']).agg(
        total_matches=('match_id', 'nunique'),
        total_balls=('is_legal', 'count'),
        total_runs=('bowler_runs', 'sum'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_dots=('is_bowler_dot', 'sum'),
        total_boundaries=('is_bowler_boundary', 'sum'),
        total_rsae=('bowl_rsae', 'sum')
    ).reset_index()
    all_bowl['overall_econ'] = all_bowl['total_runs'] / (all_bowl['total_balls'] / 6.0)
    all_bowl['overall_sr'] = all_bowl['total_balls'] / np.maximum(1, all_bowl['total_wickets'])
    all_bowl['overall_rsae6'] = (all_bowl['total_rsae'] / (all_bowl['total_balls'] / 6.0))

    # High pressure
    hp_bowl = legal_bbb[legal_bbb['is_hp'] == 1].groupby(['bowler_id', 'bowler_name']).agg(
        hp_matches=('match_id', 'nunique'),
        hp_balls=('is_legal', 'count'),
        hp_runs=('bowler_runs', 'sum'),
        hp_wickets=('is_bowler_wicket', 'sum'),
        hp_dots=('is_bowler_dot', 'sum'),
        hp_boundaries=('is_bowler_boundary', 'sum'),
        hp_rsae=('bowl_rsae', 'sum'),
        hp_wae=('bowl_wae', 'sum'),
        hp_ipl_balls=('is_ipl', 'sum')
    ).reset_index()
    hp_bowl['hp_econ'] = hp_bowl['hp_runs'] / (hp_bowl['hp_balls'] / 6.0)
    hp_bowl['hp_sr'] = hp_bowl['hp_balls'] / np.maximum(1, hp_bowl['hp_wickets'])
    hp_bowl['hp_dot_pct'] = (hp_bowl['hp_dots'] / hp_bowl['hp_balls']) * 100.0
    hp_bowl['hp_boundary_pct'] = (hp_bowl['hp_boundaries'] / hp_bowl['hp_balls']) * 100.0
    hp_bowl['hp_rsae6'] = (hp_bowl['hp_rsae'] / (hp_bowl['hp_balls'] / 6.0))  # runs saved per over vs context
    hp_bowl['hp_wae_rate'] = (hp_bowl['hp_wae'] / hp_bowl['hp_balls']) * 100.0
    hp_bowl['hp_ipl_share'] = hp_bowl['hp_ipl_balls'] / hp_bowl['hp_balls']

    # Non-HP baseline
    lp_bowl = legal_bbb[legal_bbb['is_hp'] == 0].groupby('bowler_id').agg(
        lp_balls=('is_legal', 'count'),
        lp_runs=('bowler_runs', 'sum'),
        lp_wickets=('is_bowler_wicket', 'sum'),
        lp_rsae=('bowl_rsae', 'sum')
    ).reset_index()
    lp_bowl['lp_econ'] = lp_bowl['lp_runs'] / (lp_bowl['lp_balls'] / 6.0)
    lp_bowl['lp_sr'] = lp_bowl['lp_balls'] / np.maximum(1, lp_bowl['lp_wickets'])
    lp_bowl['lp_rsae6'] = (lp_bowl['lp_rsae'] / (lp_bowl['lp_balls'] / 6.0))

    # Merge
    merged = hp_bowl.merge(lp_bowl, on='bowler_id', how='inner')
    merged = merged.merge(all_bowl[['bowler_id', 'total_matches', 'total_balls', 'total_runs', 'overall_econ', 'overall_sr', 'overall_rsae6']], on='bowler_id', how='left')

    # Filter sample size
    df = merged[(merged['hp_balls'] >= min_hp_balls) & (merged['total_balls'] >= min_total_balls)].copy()

    # Empirical Bayes Shrinkage for HP Economy and RSAE6
    K_w = 60.0
    pop_econ = df['hp_runs'].sum() / (df['hp_balls'].sum() / 6.0)
    pop_sr = df['hp_balls'].sum() / np.maximum(1, df['hp_wickets'].sum())
    pop_rsae6 = df['hp_rsae'].sum() / (df['hp_balls'].sum() / 6.0)

    df['reg_hp_econ'] = (df['hp_balls'] * df['hp_econ'] + K_w * pop_econ) / (df['hp_balls'] + K_w)
    df['reg_hp_sr'] = (df['hp_balls'] * df['hp_sr'] + K_w * pop_sr) / (df['hp_balls'] + K_w)
    df['reg_hp_rsae6'] = (df['hp_balls'] * df['hp_rsae6'] + K_w * pop_rsae6) / (df['hp_balls'] + K_w)

    # Clutch Differential
    # Economy suppression vs own baseline: positive means saving more runs under pressure
    df['clutch_rsae_delta'] = df['hp_rsae6'] - df['lp_rsae6']
    # Wicket acceleration: lower SR under pressure means positive delta
    df['clutch_sr_delta'] = df['lp_sr'] - df['hp_sr']

    # Standardized Features
    z_rsae = (df['reg_hp_rsae6'] - df['reg_hp_rsae6'].mean()) / df['reg_hp_rsae6'].std()
    z_sr = -(df['reg_hp_sr'] - df['reg_hp_sr'].mean()) / df['reg_hp_sr'].std()  # lower balls per wicket is better
    z_clutch = (df['clutch_rsae_delta'] - df['clutch_rsae_delta'].mean()) / df['clutch_rsae_delta'].std()
    z_dot = (df['hp_dot_pct'] - df['hp_dot_pct'].mean()) / df['hp_dot_pct'].std()
    z_bound = -(df['hp_boundary_pct'] - df['hp_boundary_pct'].mean()) / df['hp_boundary_pct'].std()

    # Reliability & Sample Weighting factor: sqrt(hp_balls) confidence
    sample_factor = np.clip(np.sqrt(df['hp_balls']) / np.sqrt(300), 0.85, 1.15)

    # Composite Pressure Bowling Rating (PBoR)
    # 35% Runs Saved Above Expectation (Context adjusted run suppression)
    # 25% Wicket Strike Rate under pressure (Striking when game is on the line)
    # 20% Clutch Differential (Elevation vs own baseline)
    # 10% Dot Ball Creation
    # 10% Boundary Conceded Suppression
    raw_score = (
        0.35 * z_rsae +
        0.25 * z_sr +
        0.20 * z_clutch +
        0.10 * z_dot +
        0.10 * z_bound
    )

    df['final_pbor'] = raw_score * sample_factor
    df['pressure_bowling_rating'] = 50.0 + 15.0 * (df['final_pbor'] - df['final_pbor'].mean()) / df['final_pbor'].std()

    return df.sort_values('pressure_bowling_rating', ascending=False)

top_batters = rank_batters(min_hp_balls=80, min_total_balls=200)
top_bowlers = rank_bowlers(min_hp_balls=90, min_total_balls=240)

print('\n' + '='*80)
print('TOP 15 BATTERS UNDER PRESSURE (CONTEXT ADJUSTED)')
print('='*80)
cols_bat = ['striker_name', 'hp_balls', 'hp_runs', 'hp_sr', 'lp_sr', 'clutch_sr_delta', 'hp_avg', 'hp_rae100', 'pressure_batting_rating']
print(top_batters[cols_bat].head(15).to_string(index=False))

print('\n' + '='*80)
print('TOP 15 BOWLERS UNDER PRESSURE (CONTEXT ADJUSTED)')
print('='*80)
cols_bowl = ['bowler_name', 'hp_balls', 'hp_wickets', 'hp_econ', 'lp_econ', 'hp_rsae6', 'hp_sr', 'clutch_rsae_delta', 'pressure_bowling_rating']
print(top_bowlers[cols_bowl].head(15).to_string(index=False))

