import pandas as pd
import numpy as np

import balanced_pressure as bp

bbb = bp.bbb
bbb['is_hp'] = (bbb['pressure_index'] >= 65).astype(int)

# Legal deliveries
legal_bbb = bbb[bbb['is_legal'] == 1].copy()
legal_bbb['is_boundary'] = (legal_bbb['is_four'] | legal_bbb['is_six']).astype(int)
legal_bbb['is_dot'] = (legal_bbb['runs'] == 0).astype(int)

# Bowler dot: bowler_runs == 0
legal_bbb['is_bowler_dot'] = (legal_bbb['bowler_runs'] == 0).astype(int)
legal_bbb['is_bowler_boundary'] = (legal_bbb['runs'] >= 4).astype(int)

# ==========================================
# 1. BOWLER EVALUATION
# ==========================================
def evaluate_bowlers(min_hp_balls=90, min_total_balls=240):
    # Overall
    all_bowl = legal_bbb.groupby(['bowler_id', 'bowler_name']).agg(
        total_balls=('is_legal', 'count'),
        total_runs_conceded=('bowler_runs', 'sum'),
        total_wickets=('is_bowler_wicket', 'sum'),
        total_dots=('is_bowler_dot', 'sum'),
        total_boundaries=('is_bowler_boundary', 'sum')
    ).reset_index()
    all_bowl['overall_econ'] = (all_bowl['total_runs_conceded'] / (all_bowl['total_balls'] / 6.0))
    all_bowl['overall_sr'] = all_bowl['total_balls'] / np.maximum(1, all_bowl['total_wickets'])

    # High pressure
    hp_bowl = legal_bbb[legal_bbb['is_hp'] == 1].groupby(['bowler_id', 'bowler_name']).agg(
        hp_balls=('is_legal', 'count'),
        hp_runs_conceded=('bowler_runs', 'sum'),
        hp_wickets=('is_bowler_wicket', 'sum'),
        hp_dots=('is_bowler_dot', 'sum'),
        hp_boundaries=('is_bowler_boundary', 'sum')
    ).reset_index()
    hp_bowl['hp_econ'] = (hp_bowl['hp_runs_conceded'] / (hp_bowl['hp_balls'] / 6.0))
    hp_bowl['hp_sr'] = hp_bowl['hp_balls'] / np.maximum(1, hp_bowl['hp_wickets'])
    hp_bowl['hp_dot_pct'] = (hp_bowl['hp_dots'] / hp_bowl['hp_balls']) * 100.0
    hp_bowl['hp_boundary_pct'] = (hp_bowl['hp_boundaries'] / hp_bowl['hp_balls']) * 100.0

    # Low/Medium pressure baseline (is_hp == 0)
    lp_bowl = legal_bbb[legal_bbb['is_hp'] == 0].groupby(['bowler_id', 'bowler_name']).agg(
        lp_balls=('is_legal', 'count'),
        lp_runs_conceded=('bowler_runs', 'sum'),
        lp_wickets=('is_bowler_wicket', 'sum')
    ).reset_index()
    lp_bowl['lp_econ'] = (lp_bowl['lp_runs_conceded'] / (lp_bowl['lp_balls'] / 6.0))
    lp_bowl['lp_sr'] = lp_bowl['lp_balls'] / np.maximum(1, lp_bowl['lp_wickets'])

    # Merge
    merged = hp_bowl.merge(lp_bowl, on=['bowler_id', 'bowler_name'], how='inner')
    merged = merged.merge(all_bowl[['bowler_id', 'total_balls', 'total_runs_conceded', 'overall_econ', 'overall_sr']], on='bowler_id', how='left')

    # Filter by minimum sample size
    filtered = merged[(merged['hp_balls'] >= min_hp_balls) & (merged['total_balls'] >= min_total_balls)].copy()

    # Prior means for Empirical Bayes shrinkage
    pop_hp_econ = (filtered['hp_runs_conceded'].sum() / (filtered['hp_balls'].sum() / 6.0))
    pop_hp_sr = filtered['hp_balls'].sum() / np.maximum(1, filtered['hp_wickets'].sum())

    # Bayesian shrinkage (K=60 balls)
    K = 60.0
    filtered['shrunk_hp_econ'] = (filtered['hp_balls'] * filtered['hp_econ'] + K * pop_hp_econ) / (filtered['hp_balls'] + K)
    filtered['shrunk_hp_sr'] = (filtered['hp_balls'] * filtered['hp_sr'] + K * pop_hp_sr) / (filtered['hp_balls'] + K)

    # Clutch differentials
    # Economy delta: positive means bowler CONCEDES LESS than their baseline under pressure!
    filtered['econ_delta'] = filtered['lp_econ'] - filtered['hp_econ']
    # In general T20 cricket, economy in death/pressure is naturally 2-3 runs higher than normal.
    # Relative economy index: how well they suppress runs compared to expected pressure economy
    filtered['econ_suppression'] = pop_hp_econ - filtered['hp_econ']
    filtered['wicket_delta'] = filtered['lp_sr'] - filtered['hp_sr'] # positive means faster wickets under pressure!

    # Normalized Z-scores
    # For economy: lower is better, so negate
    norm_econ = -(filtered['shrunk_hp_econ'] - pop_hp_econ) / filtered['shrunk_hp_econ'].std()
    # For wicket strike rate: lower balls per wicket is better, so negate
    norm_sr = -(filtered['shrunk_hp_sr'] - pop_hp_sr) / filtered['shrunk_hp_sr'].std()
    # For economy delta: higher lp_econ - hp_econ is better
    norm_econ_delta = (filtered['econ_delta'] - filtered['econ_delta'].mean()) / filtered['econ_delta'].std()
    # Dot %: higher is better
    norm_dot = (filtered['hp_dot_pct'] - filtered['hp_dot_pct'].mean()) / filtered['hp_dot_pct'].std()
    # Boundary % conceded: lower is better
    norm_bound = -(filtered['hp_boundary_pct'] - filtered['hp_boundary_pct'].mean()) / filtered['hp_boundary_pct'].std()

    # Composite Bowler Pressure Index (BPI_Bowl)
    filtered['bowler_bpi'] = (
        0.35 * norm_econ +
        0.25 * norm_sr +
        0.20 * norm_econ_delta +
        0.10 * norm_dot +
        0.10 * norm_bound
    )

    return filtered.sort_values('bowler_bpi', ascending=False)

bowlers = evaluate_bowlers(min_hp_balls=90, min_total_balls=240)
print('\n=== TOP 25 BOWLERS UNDER PRESSURE ===')
print(bowlers[['bowler_name', 'hp_balls', 'hp_wickets', 'hp_econ', 'lp_econ', 'econ_delta', 'hp_sr', 'lp_sr', 'hp_dot_pct', 'bowler_bpi']].head(25).to_string(index=False))

