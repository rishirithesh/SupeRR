import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression

import build_match_states as bms

bbb = bms.bbb

# 1. Fit Win Probability Model for Innings 2
inn2_mask = (bbb['innings'] == 2) & (bbb['target'].notna()) & (bbb['batting_team_won'].notna())
inn2 = bbb[inn2_mask].copy()

inn2['rpw'] = inn2['runs_required'] / np.maximum(inn2['wickets_in_hand'], 1)
features = ['runs_required', 'balls_rem', 'wickets_in_hand', 'rrr', 'rpw']
X = inn2[features].clip(lower=-50, upper=200).fillna(0)
y = inn2['batting_team_won']

wp_model = LogisticRegression(max_iter=1000)
wp_model.fit(X, y)

# Predict WP across all inn2
bbb['wp'] = np.nan
bbb.loc[inn2_mask, 'wp'] = wp_model.predict_proba(X)[:, 1]

# Leverage in Innings 2: 4 * P * (1 - P)
bbb['wp_leverage'] = np.nan
bbb.loc[inn2_mask, 'wp_leverage'] = 4.0 * bbb.loc[inn2_mask, 'wp'] * (1.0 - bbb.loc[inn2_mask, 'wp'])

# 2. Formulate Innings 2 Pressure Index (PI_inn2)
# Urgency factor based on balls bowled
urgency_inn2 = 0.40 + 0.60 * ((120 - bbb['balls_rem']) / 120.0) ** 1.5

# Rate stress: baseline T20 RRR is 8.0 rpo
rrr_clamped = bbb['rrr'].clip(lower=0, upper=24)
rate_stress = np.maximum(0, (rrr_clamped - 6.5) / 9.5)  # 0 at <=6.5, 1.0 at 16.0

# Wicket stress: extra penalty when <= 4 wickets remain
wkt_stress_inn2 = np.maximum(0, (5 - bbb['wickets_in_hand']) / 5.0)

# Closeness factor: high when match outcome is within 36 runs in the last 30 balls
closeness_inn2 = np.where(
    (bbb['balls_rem'] <= 36) & (bbb['runs_required'] <= 50) & (bbb['runs_required'] > 0),
    1.0 - np.abs(bbb['wp'] - 0.5) * 1.5,
    0.0
).clip(min=0, max=1.0)

pi_inn2 = 100.0 * (
    0.35 * (bbb['wp_leverage'].fillna(0.5) * urgency_inn2) +
    0.35 * (rate_stress * (1.0 + 0.5 * wkt_stress_inn2)).clip(0, 1.2) / 1.2 +
    0.30 * closeness_inn2
)

# 3. Formulate Innings 1 Pressure Index (PI_inn1)
# Phase stress:
# Powerplay (overs 1-6): 0.25 to 0.45
# Middle (overs 7-15): 0.35 to 0.55
# Death (overs 16-20): 0.65 to 0.95
over_num = bbb['overid']
phase_stress_inn1 = np.where(
    over_num <= 6, 0.30 + 0.02 * over_num,
    np.where(over_num <= 15, 0.42 + 0.02 * (over_num - 6),
             0.65 + 0.06 * (over_num - 15))
)

# Crisis factor: early wicket collapse in Innings 1
# Expected wickets by over t: ~ over_num / 3.5
exp_wkts = over_num / 3.5
crisis_inn1 = np.maximum(0, (bbb['cum_wickets'] - exp_wkts) / 3.5).clip(0, 1.0)

# Par-deficit pressure: venue/competition par is ~ 8.2 rpo (164 runs)
# If CRR is low and overs are passing, batting side faces escalating pressure
crr_deficit = np.maximum(0, (8.2 - bbb['crr']) / 5.0).clip(0, 1.0)
deficit_stress_inn1 = crr_deficit * (over_num / 20.0)

pi_inn1 = 100.0 * (
    0.45 * phase_stress_inn1 +
    0.35 * crisis_inn1 +
    0.20 * deficit_stress_inn1
)

# Combine Innings 1 and Innings 2 into Unified Pressure Index (PI)
bbb['pressure_index_raw'] = np.where(bbb['innings'] == 1, pi_inn1, pi_inn2)

# Knockout multiplier: 1.15x for knockout / playoff matches
ko_mult = np.where(bbb['knock_out'] == 1, 1.15, 1.0)
bbb['pressure_index'] = (bbb['pressure_index_raw'] * ko_mult).clip(0, 100)

print('\n=== PRESSURE INDEX DISTRIBUTION ===')
print(bbb['pressure_index'].describe(percentiles=[0.25, 0.50, 0.70, 0.80, 0.90, 0.95]))

# Define High Pressure: >= 65 (approx top 25-30% of deliveries)
bbb['is_high_pressure'] = (bbb['pressure_index'] >= 60).astype(int)
pct = bbb['is_high_pressure'].mean() * 100
print('\nHigh pressure balls count (PI >= 60):', bbb['is_high_pressure'].sum(), f'({pct:.1f}%)')
print('High pressure balls in Inn 1:', bbb[bbb['innings']==1]['is_high_pressure'].mean()*100, '%')
print('High pressure balls in Inn 2:', bbb[bbb['innings']==2]['is_high_pressure'].mean()*100, '%')

# Inspect sample high pressure balls
print('\nTop 10 highest pressure balls in dataset:')
top_p = bbb.sort_values('pressure_index', ascending=False).head(10)
print(top_p[['match_id', 'innings', 'overid', 'over_ball_num', 'striker_name', 'bowler_name', 'runs_required', 'balls_rem', 'rrr', 'pressure_index']])
