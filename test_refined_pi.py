import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression

import build_match_states as bms

bbb = bms.bbb

# 1. Fit Calibrated Win Probability Model for Innings 2
inn2_mask = (bbb['innings'] == 2) & (bbb['target'].notna()) & (bbb['batting_team_won'].notna())
inn2 = bbb[inn2_mask].copy()

inn2['rpw'] = inn2['runs_required'] / np.maximum(inn2['wickets_in_hand'], 1)
features = ['runs_required', 'balls_rem', 'wickets_in_hand', 'rrr', 'rpw']
X = inn2[features].clip(lower=-50, upper=200).fillna(0)
y = inn2['batting_team_won']

wp_model = LogisticRegression(max_iter=1000)
wp_model.fit(X, y)

bbb['wp'] = np.nan
bbb.loc[inn2_mask, 'wp'] = wp_model.predict_proba(X)[:, 1]

# Leverage: 4 * P * (1 - P), peaks at P = 0.50
bbb['wp_leverage'] = np.nan
bbb.loc[inn2_mask, 'wp_leverage'] = 4.0 * bbb.loc[inn2_mask, 'wp'] * (1.0 - bbb.loc[inn2_mask, 'wp'])

# 2. Refined Innings 2 Pressure Index (PI_inn2)
# In chasing:
# Component A: Closeness & Win-Probability Leverage (scaled by stage)
# Time weight: increases as match approaches finish (overs 11-20)
time_prog = (120 - bbb['balls_rem']) / 120.0
# Leverage matters more later in the innings:
lev_component = bbb['wp_leverage'].fillna(0.5) * (0.4 + 0.6 * time_prog)

# Component B: Required Run Rate & Wicket Scarcity
# Baseline RRR is 8.2. If RRR is 12, rate pressure is high. If 15, very high.
rrr_norm = np.clip((bbb['rrr'] - 6.0) / 10.0, 0.0, 1.5)  # 0 at <=6, 1.0 at 16.0
wkt_multiplier = 1.0 + np.maximum(0, (6 - bbb['wickets_in_hand']) / 6.0) * 0.5  # up to 1.5x
rate_wkt_component = np.clip(rrr_norm * wkt_multiplier, 0.0, 1.5) / 1.5

# Component C: Close finish urgency
# Within last 36 balls (overs 15-20) with target in sight (<= 60 runs)
finish_urgency = np.where(
    (bbb['balls_rem'] <= 36) & (bbb['runs_required'] > 0) & (bbb['runs_required'] <= 65),
    np.maximum(0.0, 1.0 - np.abs(bbb['wp'] - 0.5) * 1.6) * (1.0 + (36 - bbb['balls_rem'])/36.0 * 0.5),
    0.0
)
finish_urgency = np.clip(finish_urgency, 0.0, 1.5) / 1.5

# Innings 2 raw score on 0 to 100
pi_inn2_refined = 100.0 * (
    0.35 * lev_component +
    0.40 * rate_wkt_component +
    0.25 * finish_urgency
)

# 3. Refined Innings 1 Pressure Index (PI_inn1)
# In 1st innings:
# Component A: Phase Base Pressure
# Powerplay (overs 1-6): 25 to 45
# Middle (overs 7-15): 35 to 55
# Death (overs 16-20): 65 to 90
over_num = bbb['overid']
phase_base = np.where(
    over_num <= 6, 25.0 + 3.0 * over_num,
    np.where(over_num <= 15, 40.0 + 2.0 * (over_num - 6),
             60.0 + 6.0 * (over_num - 15))
)

# Component B: Early Wicket Crisis (Innings 1)
# Losing wickets early puts massive pressure on batting side
# Expected wickets: over / 3.0
exp_wkts = over_num / 3.0
crisis_boost = np.maximum(0.0, (bbb['cum_wickets'] - exp_wkts) * 7.5)  # up to +25 points
# In powerplay, if 2+ wickets down, boost:
pp_crisis = np.where((over_num <= 6) & (bbb['cum_wickets'] >= 2), (bbb['cum_wickets'] - 1) * 10.0, 0.0)

# Component C: Run-rate deficit vs par (8.2 rpo) in middle/death
crr_deficit = np.maximum(0.0, (8.2 - bbb['crr']) * 3.0) * (over_num / 20.0)

pi_inn1_refined = np.clip(phase_base + crisis_boost + pp_crisis + crr_deficit, 0.0, 100.0)

# Unify both innings
bbb['pressure_index_raw'] = np.where(bbb['innings'] == 1, pi_inn1_refined, pi_inn2_refined)

# Apply Knockout multiplier (1.15x for knockouts/playoffs)
ko_mult = np.where(bbb['knock_out'] == 1, 1.15, 1.0)
bbb['pressure_index'] = np.clip(bbb['pressure_index_raw'] * ko_mult, 0.0, 100.0)

print('\n=== REFINED PRESSURE INDEX DISTRIBUTION ===')
print(bbb['pressure_index'].describe(percentiles=[0.25, 0.50, 0.65, 0.75, 0.85, 0.90, 0.95]))

# Check High Pressure threshold at PI >= 60 and PI >= 65
for thresh in [55, 60, 65]:
    hp = (bbb['pressure_index'] >= thresh)
    pct = hp.mean() * 100
    inn1_pct = bbb[bbb['innings']==1]['pressure_index'].ge(thresh).mean() * 100
    inn2_pct = bbb[bbb['innings']==2]['pressure_index'].ge(thresh).mean() * 100
    print(f'PI >= {thresh}: {hp.sum()} deliveries ({pct:.1f}%) | Inn 1: {inn1_pct:.1f}% | Inn 2: {inn2_pct:.1f}%')
