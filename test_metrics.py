import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

bbb = pd.read_csv('ball_by_ball.csv')
matches = pd.read_csv('matches.csv')
comps = pd.read_csv('competitions.csv')

# Merge match metadata
m_meta = matches[['match_id', 'comp_id', 'win_team_id', 'revised_target', 'first_inn_revised_overs', 'second_inn_revised_overs', 'knock_out', 'result']]
bbb = bbb.merge(m_meta, on='match_id', how='left')
bbb = bbb.merge(comps[['comp_id', 'comp_name', 'match_format', 'season']], on='comp_id', how='left')

# Sort deliveries chronologically within match and innings
bbb = bbb.sort_values(['match_id', 'innings', 'overid', 'over_ball_num']).reset_index(drop=True)

# Define legal balls
bbb['is_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

# Runs on ball for team
team_runs = bbb['runs'].fillna(0).astype(int)
is_wide = (bbb['extras_type'] == 'wide').astype(int)
is_overstep = (bbb['extras_type'] == 'Overstep').astype(int)
is_lb = (bbb['extras_type'] == 'legbyes').astype(int)
is_byes = (bbb['extras_type'] == 'byes').astype(int)
is_other = (bbb['extras_type'] == 'other').astype(int)

team_runs += is_wide * 1
team_runs += is_overstep * (1 + bbb['extras_2_runs'].fillna(0).astype(int))
team_runs += is_lb * 1
team_runs += is_byes * 1
team_runs += is_other * bbb['extras_2_runs'].fillna(0).astype(int)
bbb['team_runs'] = team_runs

# Bowler conceded runs
# Bowler conceded runs = runs off bat + wide (1) + overstep (1 + extras_2_runs)
bowler_runs = bbb['runs'].fillna(0).astype(int)
bowler_runs += is_wide * 1
bowler_runs += is_overstep * (1 + bbb['extras_2_runs'].fillna(0).astype(int))
bbb['bowler_runs'] = bowler_runs

# Bowler wicket (excludes RunOut, Retire Out, Obstructing)
non_bowler_dismissals = ['RunOut', 'Retire Out', 'Obstracting the field', 'Obstructing the field']
bbb['is_bowler_wicket'] = (bbb['is_wicket'] == 1) & (~bbb['dismissal_type'].isin(non_bowler_dismissals))

print('Calculated basic delivery metrics.')
print('Total team runs:', bbb['team_runs'].sum())
print('Total bowler runs:', bbb['bowler_runs'].sum())
print('Total wickets:', bbb['is_wicket'].sum(), 'Bowler wickets:', bbb['is_bowler_wicket'].sum())

