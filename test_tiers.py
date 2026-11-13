import pandas as pd
import numpy as np

import balanced_pressure as bp

bbb = bp.bbb
bbb['is_hp'] = (bbb['pressure_index'] >= 65).astype(int)
bbb['is_ipl'] = bbb['comp_name'].str.contains('IPL', case=False, na=False).astype(int)

# Classify competition tier
top_8 = {'India', 'Australia', 'England', 'South Africa', 'New Zealand', 'West Indies', 'Pakistan', 'Sri Lanka'}
mid_tier = {'Afghanistan', 'Bangladesh', 'Ireland', 'Zimbabwe'}
associate_keywords = ['Emerging', 'Rising Stars', 'Qualifiers', 'Japan', 'Nepal', 'United Arab Emirates', 'Hong Kong', 'Netherlands']

def get_comp_tier(comp_name):
    if 'IPL' in comp_name:
        return 1.0  # Tier 1 Elite Franchise
    if any(k.lower() in comp_name.lower() for k in associate_keywords):
        return 0.75  # Tier 3 Associate / Emerging
    # Check if both teams are Top 8
    # For now, if it's Asia Cup or bilateral between top nations:
    return 0.92  # Tier 2 International Full Member

bbb['comp_weight'] = bbb['comp_name'].apply(get_comp_tier)

# Legal deliveries
legal_bbb = bbb[bbb['is_legal'] == 1].copy()
legal_bbb['is_boundary'] = (legal_bbb['is_four'] | legal_bbb['is_six']).astype(int)
legal_bbb['is_dot'] = (legal_bbb['runs'] == 0).astype(int)
legal_bbb['is_bowler_dot'] = (legal_bbb['bowler_runs'] == 0).astype(int)
legal_bbb['is_bowler_boundary'] = (legal_bbb['runs'] >= 4).astype(int)

# Weighted expectations by is_ipl and is_hp
context_stats = legal_bbb.groupby(['is_ipl', 'is_hp']).agg(
    exp_bat_runs=('runs', 'mean'),
    exp_bat_wkt=('is_wicket', 'mean'),
    exp_bowl_runs=('bowler_runs', 'mean'),
    exp_bowl_wkt=('is_bowler_wicket', 'mean')
).reset_index()

legal_bbb = legal_bbb.merge(context_stats, on=['is_ipl', 'is_hp'], how='left')

# Weighted residuals
legal_bbb['bat_rae_w'] = (legal_bbb['runs'] - legal_bbb['exp_bat_runs']) * legal_bbb['comp_weight']
legal_bbb['bowl_rsae_w'] = (legal_bbb['exp_bowl_runs'] - legal_bbb['bowler_runs']) * legal_bbb['comp_weight']
legal_bbb['bowl_wae_w'] = (legal_bbb['is_bowler_wicket'] - legal_bbb['exp_bowl_wkt']) * legal_bbb['comp_weight']

print('Tier weights applied successfully.')

