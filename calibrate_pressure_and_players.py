import pandas as pd
import numpy as np

import develop_pressure_index as dpi

bbb = dpi.bbb

# Let's inspect percentiles of pressure_index
for q in [50, 60, 70, 75, 80, 85, 90]:
    val = np.percentile(bbb['pressure_index'].dropna(), q)
    print(f'{q}th percentile: {val:.2f}')

# Let's check player counts under PI >= 50 vs PI >= 45 vs PI >= 55
for thresh in [40, 45, 50, 55]:
    sub = bbb[bbb['pressure_index'] >= thresh]
    legal_sub = sub[sub['is_legal'] == 1]
    batter_balls = legal_sub.groupby('striker_id')['is_legal'].sum()
    bowler_balls = legal_sub.groupby('bowler_id')['is_legal'].sum()
    print(f'\n--- Threshold PI >= {thresh} ---')
    print(f'Total deliveries: {len(sub)} ({len(sub)/len(bbb)*100:.1f}%)')
    print(f'Batters with >= 50 legal balls: {(batter_balls >= 50).sum()}')
    print(f'Batters with >= 100 legal balls: {(batter_balls >= 100).sum()}')
    print(f'Bowlers with >= 60 legal balls: {(bowler_balls >= 60).sum()}')
    print(f'Bowlers with >= 120 legal balls: {(bowler_balls >= 120).sum()}')

