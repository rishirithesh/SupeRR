import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

# Load and compute match states
import build_match_states as bms

bbb = bms.bbb

# Filter innings 2 deliveries with valid targets and results
inn2 = bbb[(bbb['innings'] == 2) & (bbb['target'].notna()) & (bbb['batting_team_won'].notna())].copy()

# Features for Win Probability in chase:
# 1. runs_required
# 2. balls_rem
# 3. wickets_in_hand
# 4. rrr
# 5. required runs per wicket = runs_required / np.maximum(wickets_in_hand, 1)
# 6. balls per run required = balls_rem / np.maximum(runs_required, 1)

inn2['rpw'] = inn2['runs_required'] / np.maximum(inn2['wickets_in_hand'], 1)
inn2['bpr'] = inn2['balls_rem'] / np.maximum(inn2['runs_required'], 1)

features = ['runs_required', 'balls_rem', 'wickets_in_hand', 'rrr', 'rpw']

# Handle infinite or extreme values
X = inn2[features].clip(lower=-50, upper=200).fillna(0)
y = inn2['batting_team_won']

wp_model = LogisticRegression(max_iter=1000)
wp_model.fit(X, y)

pred_probs = wp_model.predict_proba(X)[:, 1]
inn2['win_prob'] = pred_probs

print('Win Probability Model AUC:', roc_auc_score(y, pred_probs))
print('Win Probability Brier Score:', brier_score_loss(y, pred_probs))

# Win Probability Leverage: 4 * P * (1 - P) is in [0, 1]
# When P = 0.5, leverage = 1.0; when P = 0.1 or 0.9, leverage = 0.36
inn2['wp_leverage'] = 4.0 * pred_probs * (1.0 - pred_probs)

print('\nTop 5 highest leverage balls in chase sample:')
sample_high_lev = inn2.sort_values('wp_leverage', ascending=False).head(5)
print(sample_high_lev[['match_id', 'overid', 'over_ball_num', 'striker_name', 'bowler_name', 'runs_required', 'balls_rem', 'wickets_in_hand', 'rrr', 'win_prob', 'wp_leverage']])

