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

bbb['wp'] = np.nan
bbb.loc[inn2_mask, 'wp'] = wp_model.predict_proba(X)[:, 1]
bbb['wp_leverage'] = np.nan
bbb.loc[inn2_mask, 'wp_leverage'] = 4.0 * bbb.loc[inn2_mask, 'wp'] * (1.0 - bbb.loc[inn2_mask, 'wp'])

# 2. Balanced Innings 2 Pressure Index
over_num = bbb['overid']

# Phase base for Innings 2:
# Overs 1-6: 25 - 40
# Overs 7-15: 40 - 55
# Overs 16-20: 60 - 75
inn2_phase_base = np.where(
    over_num <= 6, 25.0 + 2.5 * over_num,
    np.where(over_num <= 15, 38.0 + 1.8 * (over_num - 6),
             56.0 + 4.0 * (over_num - 15))
)

# Rate delta: comparison of RRR to standard baseline 8.2 rpo
# If RRR is 12, delta is +3.8 -> substantial boost
# If RRR is 5, delta is -3.2 -> reduction
rrr_clean = bbb['rrr'].fillna(8.2).clip(0, 24)
rate_delta = (rrr_clean - 8.2) * 3.5  # +/- up to 30 points

# Wicket stress: having <= 4 wickets in hand increases pressure
wkt_stress_inn2 = np.maximum(0, (5 - bbb['wickets_in_hand'])) * 4.0  # up to +20 points

# Garbage time damper:
# If game is already decided (WP > 0.98 or WP < 0.02 and balls_rem <= 30), reduce pressure
garbage_damper = np.where(
    (bbb['balls_rem'] <= 30) & ((bbb['wp'] > 0.97) | (bbb['wp'] < 0.03)),
    0.60, 1.0
)

# Closeness surge: if balls_rem <= 24 and runs_required <= 40 and 0.15 <= WP <= 0.85
closeness_surge = np.where(
    (bbb['balls_rem'] <= 24) & (bbb['runs_required'] > 0) & (bbb['runs_required'] <= 45) & (bbb['wp'] >= 0.15) & (bbb['wp'] <= 0.85),
    15.0 * (1.0 + (24 - bbb['balls_rem']) / 24.0),
    0.0
)

pi_inn2 = np.clip((inn2_phase_base + rate_delta + wkt_stress_inn2 + closeness_surge) * garbage_damper, 0.0, 100.0)

# 3. Balanced Innings 1 Pressure Index
inn1_phase_base = np.where(
    over_num <= 6, 25.0 + 2.5 * over_num,
    np.where(over_num <= 15, 40.0 + 2.0 * (over_num - 6),
             60.0 + 5.0 * (over_num - 15))
)

# Crisis factor: early wickets in Innings 1
exp_wkts = over_num / 3.0
crisis_boost = np.maximum(0.0, (bbb['cum_wickets'] - exp_wkts) * 7.0)
pp_crisis = np.where((over_num <= 6) & (bbb['cum_wickets'] >= 2), (bbb['cum_wickets'] - 1) * 8.0, 0.0)

# Par-deficit in middle/death
crr_deficit = np.maximum(0.0, (8.2 - bbb['crr']) * 2.5) * (over_num / 20.0)

pi_inn1 = np.clip(inn1_phase_base + crisis_boost + pp_crisis + crr_deficit, 0.0, 100.0)

# Unify both innings
bbb['pressure_index_raw'] = np.where(bbb['innings'] == 1, pi_inn1, pi_inn2)

# Knockout multiplier: 1.15x for knockouts
ko_mult = np.where(bbb['knock_out'] == 1, 1.15, 1.0)
bbb['pressure_index'] = np.clip(bbb['pressure_index_raw'] * ko_mult, 0.0, 100.0)

print('\n=== BALANCED PRESSURE INDEX DISTRIBUTION ===')
print(bbb['pressure_index'].describe(percentiles=[0.25, 0.50, 0.70, 0.75, 0.80, 0.85, 0.90]))

for thresh in [55, 60, 65]:
    hp = (bbb['pressure_index'] >= thresh)
    pct = hp.mean() * 100
    inn1_pct = bbb[bbb['innings']==1]['pressure_index'].ge(thresh).mean() * 100
    inn2_pct = bbb[bbb['innings']==2]['pressure_index'].ge(thresh).mean() * 100
    print(f'PI >= {thresh}: {hp.sum()} deliveries ({pct:.1f}%) | Inn 1: {inn1_pct:.1f}% | Inn 2: {inn2_pct:.1f}%')

