import pandas as pd
import numpy as np

bbb = pd.read_csv('ball_by_ball.csv')
matches = pd.read_csv('matches.csv')

# Merge match metadata
m_meta = matches[['match_id', 'win_team_id', 'revised_target', 'first_inn_revised_overs', 'second_inn_revised_overs', 'knock_out', 'result']]
bbb = bbb.merge(m_meta, on='match_id', how='left')

# Calculate runs on each delivery for the team
# 1. Batting runs off the bat: runs
# 2. Wide: 1 extra run
# 3. Overstep: 1 extra run + extras_2_runs
# 4. Legbyes: 1 extra run
# 5. Byes: 1 extra run
# 6. Other: extras_2_runs

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
bbb['is_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

sample_mids = [13511, 13512, 13513, 13514, 13515]
for mid in sample_mids:
    res = matches[matches['match_id'] == mid]['result'].iloc[0]
    print(f'Match {mid}: Result: {res}')
    for inn in [1, 2]:
        sub = bbb[(bbb['match_id'] == mid) & (bbb['innings'] == inn)]
        tr = sub['team_runs'].sum()
        lb = sub['is_legal'].sum()
        wk = sub['is_wicket'].sum()
        print(f'  Inn {inn}: Total runs={tr}, Legal balls={lb}, Wickets={wk}')

