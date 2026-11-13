import os
import pandas as pd
import numpy as np

# Load tables
top_b = pd.read_csv('top_10_batters_under_pressure.csv')
top_bw = pd.read_csv('top_10_bowlers_under_pressure.csv')

print('Top 10 Batters:')
print(top_b[['rank', 'striker_name', 'hp_balls', 'hp_sr', 'lp_sr', 'clutch_sr_delta', 'hp_avg', 'hp_boundary_pct', 'positive_impact_pct', 'rating']])

print('\nTop 10 Bowlers:')
print(top_bw[['rank', 'bowler_name', 'hp_balls', 'hp_econ', 'lp_econ', 'hp_rsae6_w', 'hp_sr', 'hp_dot_pct', 'positive_impact_pct', 'rating']])

