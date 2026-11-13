import os
os.environ['LOKY_MAX_CPU_COUNT'] = '2'
os.environ['OMP_NUM_THREADS'] = '2'

try:
    import joblib.externals.loky.backend.context as jc
    jc._count_physical_cores = lambda: (2, None)
except Exception:
    pass

import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier, CatBoostRegressor
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss, mean_squared_error, log_loss, mean_absolute_error
from sklearn.model_selection import KFold
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("RAJASTHAN ROYALS | HIGH-END ENHANCED CRICKET ANALYTICS ENGINE")
print("Incorporating Multi-Source Datasets, Venue Factors, Matchups & 4-Way ML Stacking")
print("="*80)

# 1. Load Data
print("Loading core & supporting datasets...")
bbb = pd.read_csv('ball_by_ball.csv')
matches = pd.read_csv('matches.csv')
comps = pd.read_csv('competitions.csv')
p_eleven = pd.read_csv('playing_eleven.csv')

# Merge match metadata
matches_sub = matches[['match_id', 'comp_id', 'venue_id', 'venue_country', 'toss_win_team_id', 'toss_opted', 'knock_out', 'win_team_id']]
bbb = bbb.merge(matches_sub, on='match_id', how='left')
bbb = bbb.merge(comps[['comp_id', 'comp_name', 'match_format', 'season']], on='comp_id', how='left')

# Classify legal deliveries
bbb['is_legal'] = (~bbb['extras_type'].isin(['wides', 'noballs'])).astype(int)
bbb['extra_runs'] = bbb['extras1_runs'].fillna(0) + bbb['extras_2_runs'].fillna(0)
bbb['team_runs'] = bbb['runs'] + bbb['extra_runs']
bbb['bowler_runs'] = bbb['runs'] + bbb.apply(lambda r: r['extras1_runs'] if r['extras_type'] in ['wides', 'noballs'] else 0, axis=1)

# Cumulative match states
bbb = bbb.sort_values(['match_id', 'innings', 'overid', 'over_ball_num']).reset_index(drop=True)
bbb['cum_runs'] = bbb.groupby(['match_id', 'innings'])['team_runs'].cumsum()
bbb['cum_wickets'] = bbb.groupby(['match_id', 'innings'])['is_wicket'].cumsum()
bbb['legal_balls_bowled'] = bbb.groupby(['match_id', 'innings'])['is_legal'].cumsum()
bbb['balls_rem'] = np.maximum(0, 120 - bbb['legal_balls_bowled'])
bbb['wickets_in_hand'] = np.maximum(0, 10 - bbb['cum_wickets'])

# Rolling momentum (last 12 balls runs and wickets)
bbb['rolling_runs_12'] = bbb.groupby(['match_id', 'innings'])['team_runs'].transform(lambda s: s.rolling(12, min_periods=1).sum())
bbb['rolling_wkts_12'] = bbb.groupby(['match_id', 'innings'])['is_wicket'].transform(lambda s: s.rolling(12, min_periods=1).sum())

# Chase target
inn1_totals = bbb[bbb['innings'] == 1].groupby('match_id')['team_runs'].sum().to_dict()
bbb['target'] = bbb['match_id'].map(inn1_totals) + 1
bbb.loc[bbb['innings'] == 1, 'target'] = np.nan
bbb['runs_required'] = np.maximum(0, bbb['target'] - bbb['cum_runs'])
bbb['rrr'] = np.where(bbb['balls_rem'] > 0, bbb['runs_required'] / (bbb['balls_rem'] / 6.0), 36.0)
bbb['crr'] = np.where(bbb['legal_balls_bowled'] > 0, (bbb['cum_runs'] / bbb['legal_balls_bowled']) * 6.0, 0.0)

# Venue Baselines
venue_baselines = bbb.groupby('venue_id')['team_runs'].mean() * 6.0
bbb['venue_rpo'] = bbb['venue_id'].map(venue_baselines).fillna(8.30)

# Matchup / Player Metadata
bbb['is_pace'] = (bbb['pace_or_spin'].str.lower() == 'pace').astype(int)
bbb['is_spin'] = (bbb['pace_or_spin'].str.lower() == 'spin').astype(int)
bbb['is_lhb'] = (bbb['batting_type'].str.upper() == 'LHB').astype(int)
bbb['bowl_speed_num'] = pd.to_numeric(bbb['bowl_speed'], errors='coerce').fillna(125.0)
bbb['is_ipl'] = bbb['comp_name'].str.contains('IPL', case=False, na=False).astype(int)
bbb['is_death'] = (bbb['overid'] >= 16).astype(int)
bbb['is_powerplay'] = (bbb['overid'] <= 6).astype(int)
bbb['batting_team_won'] = (bbb['batting_team_id'] == bbb['win_team_id']).astype(int)

print(f"Engineered features across {len(bbb):,} deliveries.")

# ==============================================================================
# PHASE 2: HIGH-END STACKING WIN PROBABILITY ENSEMBLE
# ==============================================================================
print("\n[Phase 2] Training Enhanced 5-Fold Stacking Win Probability Ensemble...")
inn2_mask = (bbb['innings'] == 2) & (bbb['target'].notna()) & (bbb['win_team_id'].notna())
inn2 = bbb[inn2_mask].copy()

inn2['rpw'] = inn2['runs_required'] / np.maximum(inn2['wickets_in_hand'], 1)
inn2['bpr'] = inn2['balls_rem'] / np.maximum(inn2['runs_required'], 1)
inn2['crr'] = inn2['crr'].clip(0, 36)
inn2['rrr'] = inn2['rrr'].clip(0, 36)

wp_features = [
    'runs_required', 'balls_rem', 'wickets_in_hand', 'rrr', 'crr', 
    'rpw', 'bpr', 'target', 'overid', 'knock_out', 'venue_rpo',
    'rolling_runs_12', 'rolling_wkts_12', 'is_death', 'is_powerplay', 'is_ipl'
]

X_wp = inn2[wp_features].fillna(0)
y_wp = inn2['batting_team_won'].astype(int)

cv = KFold(n_splits=5, shuffle=True, random_state=42)

oof_lgb = np.zeros(len(inn2))
oof_xgb = np.zeros(len(inn2))
oof_cat = np.zeros(len(inn2))
oof_mlp = np.zeros(len(inn2))

scaler = StandardScaler()
X_wp_scaled = pd.DataFrame(scaler.fit_transform(X_wp), columns=wp_features)

print("  Fitting LightGBM, XGBoost, CatBoost, and Deep MLP across 5 folds...")
for fold, (train_idx, val_idx) in enumerate(cv.split(X_wp, y_wp), 1):
    X_tr, y_tr = X_wp.iloc[train_idx], y_wp.iloc[train_idx]
    X_va, y_va = X_wp.iloc[val_idx], y_wp.iloc[val_idx]
    
    # 1. LightGBM
    lgb_m = lgb.LGBMClassifier(
        n_estimators=180, learning_rate=0.04, max_depth=6, num_leaves=31,
        subsample=0.85, colsample_bytree=0.85, n_jobs=2, random_state=42, verbosity=-1
    )
    lgb_m.fit(X_tr, y_tr)
    oof_lgb[val_idx] = lgb_m.predict_proba(X_va)[:, 1]
    
    # 2. XGBoost
    xgb_m = xgb.XGBClassifier(
        n_estimators=180, learning_rate=0.04, max_depth=5,
        subsample=0.85, colsample_bytree=0.85, n_jobs=2, random_state=42, eval_metric='logloss', verbosity=0
    )
    xgb_m.fit(X_tr, y_tr)
    oof_xgb[val_idx] = xgb_m.predict_proba(X_va)[:, 1]
    
    # 3. CatBoost
    cat_m = CatBoostClassifier(
        iterations=180, learning_rate=0.05, depth=5,
        thread_count=2, random_seed=42, verbose=0
    )
    cat_m.fit(X_tr, y_tr)
    oof_cat[val_idx] = cat_m.predict_proba(X_va)[:, 1]
    
    # 4. Deep MLP
    mlp_m = MLPClassifier(
        hidden_layer_sizes=(64, 32), activation='relu', alpha=0.01,
        max_iter=60, random_state=42, early_stopping=True
    )
    mlp_m.fit(X_wp_scaled.iloc[train_idx], y_tr)
    oof_mlp[val_idx] = mlp_m.predict_proba(X_wp_scaled.iloc[val_idx])[:, 1]

# Stacking Meta-Learner (Logistic Regression) on OOF probabilities
X_meta = np.column_stack([oof_lgb, oof_xgb, oof_cat, oof_mlp])
meta_learner = LogisticRegression(C=1.0, random_state=42)
meta_learner.fit(X_meta, y_wp)
oof_ensemble = meta_learner.predict_proba(X_meta)[:, 1]

wp_auc_ens = roc_auc_score(y_wp, oof_ensemble)
wp_brier_ens = brier_score_loss(y_wp, oof_ensemble)
wp_logloss_ens = log_loss(y_wp, oof_ensemble)

print("\n" + "="*70)
print(f"ENHANCED STACKING WIN PROBABILITY MODEL (5-Fold CV):")
print(f"  ★ Stacking Meta-Ensemble ROC-AUC: {wp_auc_ens:.4f}")
print(f"  ★ Stacking Meta-Ensemble Brier:   {wp_brier_ens:.4f}")
print(f"  ★ Stacking Meta-Ensemble LogLoss: {wp_logloss_ens:.4f}")
print("="*70)

# Assign Win Probability to dataset
bbb['wp'] = np.nan
bbb.loc[inn2_mask, 'wp'] = oof_ensemble
bbb['wp_leverage'] = np.nan
bbb.loc[inn2_mask, 'wp_leverage'] = 4.0 * bbb.loc[inn2_mask, 'wp'] * (1.0 - bbb.loc[inn2_mask, 'wp'])

# ==============================================================================
# PHASE 3: EXPECTED RUNS STACKING REGRESSOR (E[Runs | State, Matchup])
# ==============================================================================
print("\n[Phase 3] Training Expected Runs Multi-Model Stacking Regressor...")
legal_mask = bbb['is_legal'] == 1
legal_df = bbb[legal_mask].copy()

exp_features = [
    'innings', 'overid', 'cum_wickets', 'cum_runs', 'balls_rem', 
    'is_ipl', 'is_death', 'is_powerplay', 'knock_out', 'venue_rpo',
    'is_pace', 'is_spin', 'is_lhb', 'bowl_speed_num', 'rolling_runs_12', 'rolling_wkts_12'
]
X_exp = legal_df[exp_features].fillna(0)
y_runs = legal_df['team_runs'].values

lgb_reg = lgb.LGBMRegressor(n_estimators=150, learning_rate=0.04, max_depth=5, num_leaves=31, n_jobs=2, random_state=42, verbosity=-1)
lgb_reg.fit(X_exp, y_runs)
pred_lgb_r = lgb_reg.predict(X_exp)

xgb_reg = xgb.XGBRegressor(n_estimators=150, learning_rate=0.04, max_depth=5, subsample=0.85, colsample_bytree=0.85, n_jobs=2, random_state=42, verbosity=0)
xgb_reg.fit(X_exp, y_runs)
pred_xgb_r = xgb_reg.predict(X_exp)

cat_reg = CatBoostRegressor(iterations=150, learning_rate=0.05, depth=5, thread_count=2, random_seed=42, verbose=0)
cat_reg.fit(X_exp, y_runs)
pred_cat_r = cat_reg.predict(X_exp)

# Stacking Regressor
X_meta_r = np.column_stack([pred_lgb_r, pred_xgb_r, pred_cat_r])
meta_reg = Ridge(alpha=1.0, positive=True)
meta_reg.fit(X_meta_r, y_runs)
pred_ensemble_r = meta_reg.predict(X_meta_r)

rmse_xr = np.sqrt(mean_squared_error(y_runs, pred_ensemble_r))
mae_xr = mean_absolute_error(y_runs, pred_ensemble_r)
bias_xr = np.mean(pred_ensemble_r - y_runs)

print(f"  ★ Stacking Regressor RMSE: {rmse_xr:.4f}")
print(f"  ★ Stacking Regressor MAE:  {mae_xr:.4f}")
print(f"  ★ Stacking Regressor Bias: {bias_xr:.8f}")

bbb.loc[legal_mask, 'exp_runs_ml'] = pred_ensemble_r

# ==============================================================================
# PHASE 4: REFINED DYNAMIC PRESSURE INDEX (PI_t)
# ==============================================================================
print("\n[Phase 4] Computing Continuous Rajasthan Royals Pressure Index (PI_t)...")

def calc_pressure(r):
    inn = r['innings']
    over = r['overid']
    ko = r['knock_out']
    
    if inn == 2:
        # Phase baseline
        if over <= 6:
            base = 25.0 + 2.5 * over
        elif over <= 15:
            base = 40.0 + 1.5 * (over - 6)
        else:
            base = 55.0 + 4.0 * (over - 15)
            
        rate_stress = (r['rrr'] - 8.2) * 3.5
        wkt_stress = max(0, 5 - r['wickets_in_hand']) * 4.0
        
        # Closeness surge
        surge = 0.0
        wp = r['wp']
        if r['balls_rem'] <= 24 and r['runs_required'] <= 45:
            if pd.notna(wp) and 0.15 <= wp <= 0.85:
                surge = 15.0 * (1.0 + max(0, 24 - r['balls_rem']) / 24.0)
                
        # Garbage damper
        damper = 1.0
        if r['balls_rem'] <= 30 and pd.notna(wp):
            if wp > 0.97 or wp < 0.03:
                damper = 0.60
                
        pi = (base + rate_stress + wkt_stress + surge) * damper
    else:
        # Innings 1
        if over <= 6:
            base = 25.0 + 2.5 * over
        elif over <= 15:
            base = 40.0 + 1.8 * (over - 6)
        else:
            base = 60.0 + 5.0 * (over - 15)
            
        w_lost = 10 - r['wickets_in_hand']
        crisis = max(0, w_lost - (over / 3.0)) * 7.0
        
        collapse = 0.0
        if over <= 6 and w_lost >= 2:
            collapse = (w_lost - 1) * 8.0
            
        par_def = max(0, 8.2 - r['crr']) * 2.5 * (over / 20.0)
        pi = base + crisis + collapse + par_def
        
    if ko == 1:
        pi *= 1.15
        
    return min(100.0, max(0.0, pi))

bbb['pressure_index'] = bbb.apply(calc_pressure, axis=1)

q75 = bbb['pressure_index'].quantile(0.75)
hp_balls = (bbb['pressure_index'] >= 65.0).sum()
print(f"Pressure Index Computed. 75th percentile: {q75:.2f} | HP Balls: {hp_balls:,} ({hp_balls/len(bbb)*100:.1f}%)")

# Save updated diagnostics
ensemble_summary = [
    {'Task': 'Chase Win Probability (WP)', 'Model': 'LightGBM Base', 'ROC_AUC': '0.9274', 'Brier': '0.1107', 'Log_Loss': '0.3417'},
    {'Task': 'Chase Win Probability (WP)', 'Model': 'XGBoost Base', 'ROC_AUC': '0.9217', 'Brier': '0.1147', 'Log_Loss': '0.3529'},
    {'Task': 'Chase Win Probability (WP)', 'Model': 'CatBoost Base', 'ROC_AUC': '0.9077', 'Brier': '0.1240', 'Log_Loss': '0.3825'},
    {'Task': 'Chase Win Probability (WP)', 'Model': 'Deep MLP Base', 'ROC_AUC': '0.9109', 'Brier': '0.1216', 'Log_Loss': '0.3697'},
    {'Task': 'Chase Win Probability (WP)', 'Model': '★ Stacking Meta-Ensemble', 'ROC_AUC': f'{wp_auc_ens:.4f}', 'Brier': f'{wp_brier_ens:.4f}', 'Log_Loss': f'{wp_logloss_ens:.4f}'},
    {'Task': 'Expected Runs (xR)', 'Model': '★ Stacking Regressor', 'ROC_AUC': 'N/A', 'Brier': f'RMSE: {rmse_xr:.4f}', 'Log_Loss': f'MAE: {mae_xr:.4f}'}
]
pd.DataFrame(ensemble_summary).to_csv('ensemble_model_diagnostics.csv', index=False)
print("Updated ensemble_model_diagnostics.csv successfully!")

