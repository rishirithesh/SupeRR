import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, brier_score_loss, mean_squared_error, log_loss
from sklearn.model_selection import KFold
import warnings
warnings.filterwarnings('ignore')

import balanced_pressure as bp

print('Initializing Advanced ML Analytics Engine...')
bbb = bp.bbb

# 1. Feature Engineering for Win Probability (Chase - Innings 2)
inn2_mask = (bbb['innings'] == 2) & (bbb['target'].notna()) & (bbb['batting_team_won'].notna())
inn2 = bbb[inn2_mask].copy()

inn2['rpw'] = inn2['runs_required'] / np.maximum(inn2['wickets_in_hand'], 1)
inn2['bpr'] = inn2['balls_rem'] / np.maximum(inn2['runs_required'], 1)
inn2['crr'] = inn2['crr'].clip(0, 36)
inn2['rrr'] = inn2['rrr'].clip(0, 36)
inn2['is_death'] = (inn2['overid'] >= 16).astype(int)
inn2['is_powerplay'] = (inn2['overid'] <= 6).astype(int)

wp_features = [
    'runs_required', 'balls_rem', 'wickets_in_hand', 'rrr', 'crr', 
    'rpw', 'bpr', 'target', 'overid', 'knock_out'
]

X_wp = inn2[wp_features].fillna(0)
y_wp = inn2['batting_team_won']

# 5-fold CV for LightGBM Win Probability Model
cv = KFold(n_splits=5, shuffle=True, random_state=42)
oof_wp = np.zeros(len(inn2))

for train_idx, val_idx in cv.split(X_wp, y_wp):
    X_train, y_train = X_wp.iloc[train_idx], y_wp.iloc[train_idx]
    X_val, y_val = X_wp.iloc[val_idx], y_wp.iloc[val_idx]
    
    model = lgb.LGBMClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=5,
        num_leaves=31,
        random_state=42,
        verbosity=-1
    )
    model.fit(X_train, y_train)
    oof_wp[val_idx] = model.predict_proba(X_val)[:, 1]

wp_auc = roc_auc_score(y_wp, oof_wp)
wp_brier = brier_score_loss(y_wp, oof_wp)
wp_logloss = log_loss(y_wp, oof_wp)

print(f'LightGBM Win Probability Model — 5-Fold CV:')
print(f'  ROC-AUC:   {wp_auc:.4f}')
print(f'  Brier:     {wp_brier:.4f}')
print(f'  Log-Loss:  {wp_logloss:.4f}')

# Train final WP model
final_wp_model = lgb.LGBMClassifier(
    n_estimators=150, learning_rate=0.05, max_depth=5, num_leaves=31, random_state=42, verbosity=-1
)
final_wp_model.fit(X_wp, y_wp)
bbb['ml_win_prob'] = np.nan
bbb.loc[inn2_mask, 'ml_win_prob'] = final_wp_model.predict_proba(X_wp)[:, 1]

# Leverage Index: 4 * P * (1 - P)
bbb['ml_wp_leverage'] = np.nan
bbb.loc[inn2_mask, 'ml_wp_leverage'] = 4.0 * bbb.loc[inn2_mask, 'ml_win_prob'] * (1.0 - bbb.loc[inn2_mask, 'ml_win_prob'])

# 2. LightGBM Expected Runs Model (E[Runs | State])
# Trained across all legal deliveries
legal_mask = bbb['is_legal'] == 1
legal_df = bbb[legal_mask].copy()

# Features for Expected Runs & Wickets
legal_df['is_ipl'] = legal_df['comp_name'].str.contains('IPL', case=False, na=False).astype(int)
legal_df['is_death'] = (legal_df['overid'] >= 16).astype(int)
legal_df['is_powerplay'] = (legal_df['overid'] <= 6).astype(int)

exp_features = [
    'innings', 'overid', 'cum_wickets', 'cum_runs', 'balls_rem', 
    'is_ipl', 'is_death', 'is_powerplay', 'knock_out'
]
X_exp = legal_df[exp_features].fillna(0)
y_runs = legal_df['team_runs']
y_wkt = legal_df['is_wicket']

# Train Expected Runs Model (Regressor)
runs_model = lgb.LGBMRegressor(
    n_estimators=120, learning_rate=0.05, max_depth=4, num_leaves=20, random_state=42, verbosity=-1
)
runs_model.fit(X_exp, y_runs)
legal_df['exp_runs_ml'] = runs_model.predict(X_exp)

# Train Expected Wicket Hazard Model (Classifier)
wkt_model = lgb.LGBMClassifier(
    n_estimators=120, learning_rate=0.05, max_depth=4, num_leaves=20, random_state=42, verbosity=-1
)
wkt_model.fit(X_exp, y_wkt)
legal_df['exp_wkt_prob_ml'] = wkt_model.predict_proba(X_exp)[:, 1]

print('Trained LightGBM Expected Runs (xR) and Expected Wickets (xW) models.')
mean_exp_r = legal_df["exp_runs_ml"].mean()
mean_act_r = legal_df["team_runs"].mean()
mean_exp_w = legal_df["exp_wkt_prob_ml"].mean()
mean_act_w = legal_df["is_wicket"].mean()
print(f'Mean Expected Runs per ball: {mean_exp_r:.3f} (Actual: {mean_act_r:.3f})')
print(f'Mean Expected Wicket Prob:   {mean_exp_w:.4f} (Actual: {mean_act_w:.4f})')

# Feature Importances
feat_imp_wp = pd.Series(final_wp_model.feature_importances_, index=wp_features).sort_values(ascending=False)
feat_imp_xr = pd.Series(runs_model.feature_importances_, index=exp_features).sort_values(ascending=False)
print('\nTop Features for Win Probability:')
print(feat_imp_wp.head(5))
print('\nTop Features for Expected Runs (xR):')
print(feat_imp_xr.head(5))

# Export ML Diagnostics to CSV for LaTeX inclusion
rmse_runs = np.sqrt(mean_squared_error(y_runs, legal_df['exp_runs_ml']))
mae_runs = np.mean(np.abs(y_runs - legal_df['exp_runs_ml']))
bias_runs = np.mean(legal_df['exp_runs_ml'] - y_runs)
auc_wkt = roc_auc_score(y_wkt, legal_df['exp_wkt_prob_ml'])
brier_wkt = brier_score_loss(y_wkt, legal_df['exp_wkt_prob_ml'])
logloss_wkt = log_loss(y_wkt, legal_df['exp_wkt_prob_ml'])

ml_diag = pd.DataFrame([{
    'Model': 'Win Probability (LightGBM)',
    'Task': 'Binary Classification',
    'Metric_1': f'ROC-AUC: {wp_auc:.4f}',
    'Metric_2': f'Brier Score: {wp_brier:.4f}',
    'Metric_3': f'Log-Loss: {wp_logloss:.4f}',
    'Key_Predictors': 'rrr, rpw, balls_rem, runs_required'
}, {
    'Model': 'Expected Runs xR (LightGBM)',
    'Task': 'Gradient Boosted Regression',
    'Metric_1': f'RMSE: {rmse_runs:.4f}',
    'Metric_2': f'MAE: {mae_runs:.4f}',
    'Metric_3': f'Mean Bias: {bias_runs:.6f}',
    'Key_Predictors': 'overid, is_death, cum_wickets, is_ipl'
}, {
    'Model': 'Wicket Hazard xW (LightGBM)',
    'Task': 'Probability Calibration',
    'Metric_1': f'ROC-AUC: {auc_wkt:.4f}',
    'Metric_2': f'Brier Score: {brier_wkt:.4f}',
    'Metric_3': f'Log-Loss: {logloss_wkt:.4f}',
    'Key_Predictors': 'cum_wickets, overid, is_death, balls_rem'
}])
ml_diag.to_csv('ml_model_diagnostics.csv', index=False)
print('\nExported ml_model_diagnostics.csv')
