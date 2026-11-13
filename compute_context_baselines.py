import pandas as pd
import numpy as np

import balanced_pressure as bp

bbb = bp.bbb
bbb['is_hp'] = (bbb['pressure_index'] >= 65).astype(int)
bbb['is_ipl'] = bbb['comp_name'].str.contains('IPL', case=False, na=False).astype(int)

# Group by is_ipl, is_hp to check expectations
legal_bbb = bbb[bbb['is_legal'] == 1].copy()

legal_bbb['is_bowler_dot'] = (legal_bbb['bowler_runs'] == 0).astype(int)
legal_bbb['is_boundary'] = (legal_bbb['is_four'] | legal_bbb['is_six']).astype(int)
legal_bbb['is_dot'] = (legal_bbb['runs'] == 0).astype(int)

print('=== BATTING EXPECTATIONS BY CONTEXT ===')
bat_exp = legal_bbb.groupby(['is_ipl', 'is_hp']).agg(
    balls=('runs', 'count'),
    mean_runs_per_ball=('runs', 'mean'),
    dismissal_rate=('is_wicket', 'mean'),
    boundary_rate=('is_boundary', 'mean'),
    dot_rate=('is_dot', 'mean')
).reset_index()
bat_exp['expected_sr'] = bat_exp['mean_runs_per_ball'] * 100.0
bat_exp['expected_rpo'] = bat_exp['mean_runs_per_ball'] * 6.0
print(bat_exp.to_string(index=False))

print('\n=== BOWLING EXPECTATIONS BY CONTEXT ===')
bowl_exp = legal_bbb.groupby(['is_ipl', 'is_hp']).agg(
    balls=('bowler_runs', 'count'),
    mean_runs_conceded_per_ball=('bowler_runs', 'mean'),
    wicket_rate=('is_bowler_wicket', 'mean'),
    dot_rate=('is_bowler_dot', 'mean')
).reset_index()
bowl_exp['expected_econ'] = bowl_exp['mean_runs_conceded_per_ball'] * 6.0
bowl_exp['expected_balls_per_wicket'] = 1.0 / np.maximum(1e-6, bowl_exp['wicket_rate'])
print(bowl_exp.to_string(index=False))
