import pandas as pd
import numpy as np
import time

t0 = time.time()
print('Loading datasets...')
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
bowler_runs = bbb['runs'].fillna(0).astype(int)
bowler_runs += is_wide * 1
bowler_runs += is_overstep * (1 + bbb['extras_2_runs'].fillna(0).astype(int))
bbb['bowler_runs'] = bowler_runs

# Bowler wicket
non_bowler_dismissals = ['RunOut', 'Retire Out', 'Obstracting the field', 'Obstructing the field']
bbb['is_bowler_wicket'] = (bbb['is_wicket'] == 1) & (~bbb['dismissal_type'].isin(non_bowler_dismissals))

# Vectorized cumulative state per match and innings
print('Computing cumulative states...')
grouped = bbb.groupby(['match_id', 'innings'])

# State BEFORE the ball
bbb['cum_runs'] = grouped['team_runs'].cumsum() - bbb['team_runs']
bbb['cum_wickets'] = grouped['is_wicket'].cumsum() - bbb['is_wicket']
bbb['cum_legal_balls'] = grouped['is_legal'].cumsum() - bbb['is_legal']

# Innings 1 total runs per match
inn1_totals = bbb[bbb['innings'] == 1].groupby('match_id')['team_runs'].sum().rename('inn1_total_runs')
bbb = bbb.merge(inn1_totals, on='match_id', how='left')

# Scheduled overs / balls per innings
# If first_inn_revised_overs is present, use it for inn 1, else 20
bbb['max_overs_inn1'] = bbb['first_inn_revised_overs'].fillna(20.0)
bbb['max_overs_inn2'] = bbb['second_inn_revised_overs'].fillna(20.0)
bbb['max_balls_inn1'] = (bbb['max_overs_inn1'] * 6).astype(int)
bbb['max_balls_inn2'] = (bbb['max_overs_inn2'] * 6).astype(int)

# Set target for innings 2
# If revised_target is present, use it, else inn1_total_runs + 1
bbb['target'] = np.where(bbb['revised_target'].notna(), bbb['revised_target'], bbb['inn1_total_runs'] + 1)

# Balls remaining and wickets in hand before delivery
bbb['balls_rem'] = np.where(
    bbb['innings'] == 1,
    np.maximum(0, bbb['max_balls_inn1'] - bbb['cum_legal_balls']),
    np.maximum(0, bbb['max_balls_inn2'] - bbb['cum_legal_balls'])
)
bbb['wickets_in_hand'] = 10 - bbb['cum_wickets']

# Runs required in innings 2
bbb['runs_required'] = np.where(
    bbb['innings'] == 2,
    np.maximum(0, bbb['target'] - bbb['cum_runs']),
    np.nan
)

# Required Run Rate in innings 2
# Avoid division by zero: if balls_rem == 0, use 1 ball
safe_overs_rem = np.maximum(bbb['balls_rem'] / 6.0, 1.0 / 6.0)
bbb['rrr'] = np.where(
    bbb['innings'] == 2,
    bbb['runs_required'] / safe_overs_rem,
    np.nan
)

# Current Run Rate
safe_overs_bowled = np.maximum(bbb['cum_legal_balls'] / 6.0, 1.0 / 6.0)
bbb['crr'] = bbb['cum_runs'] / safe_overs_bowled

# Did batting team win the match?
bbb['batting_team_won'] = (bbb['win_team_id'] == bbb['batting_team_id']).astype(int)

print(f'Done in {time.time()-t0:.2f}s')
print('Sample innings 2 balls:')
print(bbb[bbb['innings'] == 2][['match_id', 'overid', 'over_ball_num', 'striker_name', 'cum_runs', 'cum_wickets', 'target', 'runs_required', 'balls_rem', 'rrr']].head(10))

