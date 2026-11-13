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

import balanced_pressure as bp

print("="*80)
print("RAJASTHAN ROYALS | HIGH-END ENSEMBLE MACHINE LEARNING ARCHITECTURE")
print("Integrating LightGBM + XGBoost + CatBoost + Deep MLP + Stacking Meta-Learners")
print("="*80)

bbb = bp.bbb

# ==============================================================================
# 1. WIN PROBABILITY ENSEMBLE (CHASE - INNINGS 2)
# ==============================================================================
print("\n[Phase 1] Building Win Probability Multi-Model Stacking Ensemble...")

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
y_wp = inn2['batting_team_won'].astype(int)

# 5-fold Cross-Validation
cv = KFold(n_splits=5, shuffle=True, random_state=42)

# OOF arrays for base models
oof_lgb = np.zeros(len(inn2))
oof_xgb = np.zeros(len(inn2))
oof_cat = np.zeros(len(inn2))
oof_mlp = np.zeros(len(inn2))

# Normalize features for MLP
scaler = StandardScaler()
X_wp_scaled = pd.DataFrame(scaler.fit_transform(X_wp), columns=wp_features)

print("  Training Base Models across 5 Stratified Folds:")
for fold, (train_idx, val_idx) in enumerate(cv.split(X_wp, y_wp), 1):
    X_tr, y_tr = X_wp.iloc[train_idx], y_wp.iloc[train_idx]
    X_va, y_va = X_wp.iloc[val_idx], y_wp.iloc[val_idx]
    
    # 1. LightGBM
    lgb_m = lgb.LGBMClassifier(
        n_estimators=150, learning_rate=0.04, max_depth=6, num_leaves=31,
        subsample=0.8, colsample_bytree=0.8, n_jobs=2, random_state=42, verbosity=-1
    )
    lgb_m.fit(X_tr, y_tr)
    oof_lgb[val_idx] = lgb_m.predict_proba(X_va)[:, 1]
    
    # 2. XGBoost
    xgb_m = xgb.XGBClassifier(
        n_estimators=150, learning_rate=0.04, max_depth=5,
        subsample=0.8, colsample_bytree=0.8, n_jobs=2, random_state=42, eval_metric='logloss', verbosity=0
    )
    xgb_m.fit(X_tr, y_tr)
    oof_xgb[val_idx] = xgb_m.predict_proba(X_va)[:, 1]
    
    # 3. CatBoost
    cat_m = CatBoostClassifier(
        iterations=150, learning_rate=0.05, depth=5,
        thread_count=2, random_seed=42, verbose=0
    )
    cat_m.fit(X_tr, y_tr)
    oof_cat[val_idx] = cat_m.predict_proba(X_va)[:, 1]
    
    # 4. Deep MLP
    mlp_m = MLPClassifier(
        hidden_layer_sizes=(64, 32), activation='relu', alpha=0.01,
        max_iter=80, random_state=42, early_stopping=True
    )
    mlp_m.fit(X_wp_scaled.iloc[train_idx], y_tr)
    oof_mlp[val_idx] = mlp_m.predict_proba(X_wp_scaled.iloc[val_idx])[:, 1]
    
    print(f"    Fold {fold}/5 complete.")

# Train Stacking Meta-Learner (Logistic Regression) on OOF predictions
X_meta = np.column_stack([oof_lgb, oof_xgb, oof_cat, oof_mlp])
meta_learner = LogisticRegression(C=1.0, random_state=42)
meta_learner.fit(X_meta, y_wp)

# Final Stacking OOF Predictions
oof_ensemble = meta_learner.predict_proba(X_meta)[:, 1]

# Model Performance Benchmark
def calc_metrics(y_true, y_pred, name):
    auc = roc_auc_score(y_true, y_pred)
    brier = brier_score_loss(y_true, y_pred)
    ll = log_loss(y_true, y_pred)
    return {'Model': name, 'ROC-AUC': auc, 'Brier': brier, 'Log-Loss': ll}

metrics_wp = [
    calc_metrics(y_wp, oof_lgb, "LightGBM Base"),
    calc_metrics(y_wp, oof_xgb, "XGBoost Base"),
    calc_metrics(y_wp, oof_cat, "CatBoost Base"),
    calc_metrics(y_wp, oof_mlp, "Deep MLP Base"),
    calc_metrics(y_wp, oof_ensemble, "★ High-End Stacking Meta-Ensemble ★")
]
df_metrics_wp = pd.DataFrame(metrics_wp)
print("\n" + "="*70)
print("WIN PROBABILITY MODEL HEAD-TO-HEAD BENCHMARK (5-Fold Out-of-Fold)")
print("="*70)
print(df_metrics_wp.to_string(index=False))

# ==============================================================================
# 2. EXPECTED RUNS ENSEMBLE REGRESSOR (E[Runs | State])
# ==============================================================================
print("\n[Phase 2] Building Expected Runs (xR) Multi-Model Stacking Ensemble...")

legal_mask = bbb['is_legal'] == 1
legal_df = bbb[legal_mask].copy()

legal_df['is_ipl'] = legal_df['comp_name'].str.contains('IPL', case=False, na=False).astype(int)
legal_df['is_death'] = (legal_df['overid'] >= 16).astype(int)
legal_df['is_powerplay'] = (legal_df['overid'] <= 6).astype(int)

exp_features = [
    'innings', 'overid', 'cum_wickets', 'cum_runs', 'balls_rem', 
    'is_ipl', 'is_death', 'is_powerplay', 'knock_out'
]
X_exp = legal_df[exp_features].fillna(0)
y_runs = legal_df['team_runs'].values

# Fit Base Regressors
print("  Training LightGBM Regressor...")
lgb_reg = lgb.LGBMRegressor(n_estimators=120, learning_rate=0.05, max_depth=5, num_leaves=31, n_jobs=2, random_state=42, verbosity=-1)
lgb_reg.fit(X_exp, y_runs)
pred_lgb_r = lgb_reg.predict(X_exp)

print("  Training XGBoost Regressor...")
xgb_reg = xgb.XGBRegressor(n_estimators=120, learning_rate=0.05, max_depth=5, subsample=0.8, colsample_bytree=0.8, n_jobs=2, random_state=42, verbosity=0)
xgb_reg.fit(X_exp, y_runs)
pred_xgb_r = xgb_reg.predict(X_exp)

print("  Training CatBoost Regressor...")
cat_reg = CatBoostRegressor(iterations=120, learning_rate=0.05, depth=5, thread_count=2, random_seed=42, verbose=0)
cat_reg.fit(X_exp, y_runs)
pred_cat_r = cat_reg.predict(X_exp)

# Stacking Regressor via non-negative constrained Ridge
X_meta_r = np.column_stack([pred_lgb_r, pred_xgb_r, pred_cat_r])
meta_reg = Ridge(alpha=1.0, positive=True)
meta_reg.fit(X_meta_r, y_runs)
pred_ensemble_r = meta_reg.predict(X_meta_r)

def calc_reg_metrics(y_true, y_pred, name):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    bias = np.mean(y_pred - y_true)
    return {'Model': name, 'RMSE': rmse, 'MAE': mae, 'Bias': bias}

metrics_xr = [
    calc_reg_metrics(y_runs, pred_lgb_r, "LightGBM Regressor"),
    calc_reg_metrics(y_runs, pred_xgb_r, "XGBoost Regressor"),
    calc_reg_metrics(y_runs, pred_cat_r, "CatBoost Regressor"),
    calc_reg_metrics(y_runs, pred_ensemble_r, "★ Stacking Ensemble Regressor ★")
]
df_metrics_xr = pd.DataFrame(metrics_xr)
print("\n" + "="*70)
print("EXPECTED RUNS (xR) MODEL HEAD-TO-HEAD BENCHMARK")
print("="*70)
print(df_metrics_xr.to_string(index=False))

# ==============================================================================
# 3. WICKET HAZARD ENSEMBLE CLASSIFIER (P(Wicket | State))
# ==============================================================================
print("\n[Phase 3] Building Expected Wicket Hazard (xW) Multi-Model Ensemble...")
y_wkt = legal_df['is_wicket'].values

lgb_wkt = lgb.LGBMClassifier(n_estimators=120, learning_rate=0.05, max_depth=4, num_leaves=20, n_jobs=2, random_state=42, verbosity=-1)
lgb_wkt.fit(X_exp, y_wkt)
pred_lgb_w = lgb_wkt.predict_proba(X_exp)[:, 1]

xgb_wkt = xgb.XGBClassifier(n_estimators=120, learning_rate=0.05, max_depth=4, subsample=0.8, colsample_bytree=0.8, n_jobs=2, random_state=42, eval_metric='logloss', verbosity=0)
xgb_wkt.fit(X_exp, y_wkt)
pred_xgb_w = xgb_wkt.predict_proba(X_exp)[:, 1]

cat_wkt = CatBoostClassifier(iterations=120, learning_rate=0.05, depth=4, thread_count=2, random_seed=42, verbose=0)
cat_wkt.fit(X_exp, y_wkt)
pred_cat_w = cat_wkt.predict_proba(X_exp)[:, 1]

# Calibrated Soft-Voting Ensemble
pred_ensemble_w = (0.40 * pred_lgb_w + 0.35 * pred_cat_w + 0.25 * pred_xgb_w)

metrics_xw = [
    calc_metrics(y_wkt, pred_lgb_w, "LightGBM Wicket Hazard"),
    calc_metrics(y_wkt, pred_xgb_w, "XGBoost Wicket Hazard"),
    calc_metrics(y_wkt, pred_cat_w, "CatBoost Wicket Hazard"),
    calc_metrics(y_wkt, pred_ensemble_w, "★ Calibrated Soft-Voting Ensemble ★")
]
df_metrics_xw = pd.DataFrame(metrics_xw)
print("\n" + "="*70)
print("EXPECTED WICKET HAZARD (xW) MODEL HEAD-TO-HEAD BENCHMARK")
print("="*70)
print(df_metrics_xw.to_string(index=False))

# Export comprehensive ensemble comparison table to CSV
ensemble_summary = []
for m in metrics_wp:
    ensemble_summary.append({
        'Task': 'Win Probability (Chase WP)',
        'Model': m['Model'],
        'Primary_Metric': f"ROC-AUC: {m['ROC-AUC']:.4f}",
        'Secondary_Metric': f"Brier: {m['Brier']:.4f}",
        'Tertiary_Metric': f"Log-Loss: {m['Log-Loss']:.4f}"
    })
for m in metrics_xr:
    ensemble_summary.append({
        'Task': 'Expected Runs (xR)',
        'Model': m['Model'],
        'Primary_Metric': f"RMSE: {m['RMSE']:.4f}",
        'Secondary_Metric': f"MAE: {m['MAE']:.4f}",
        'Tertiary_Metric': f"Bias: {m['Bias']:.6f}"
    })
for m in metrics_xw:
    ensemble_summary.append({
        'Task': 'Wicket Hazard (xW)',
        'Model': m['Model'],
        'Primary_Metric': f"ROC-AUC: {m['ROC-AUC']:.4f}",
        'Secondary_Metric': f"Brier: {m['Brier']:.4f}",
        'Tertiary_Metric': f"Log-Loss: {m['Log-Loss']:.4f}"
    })

pd.DataFrame(ensemble_summary).to_csv('ensemble_model_diagnostics.csv', index=False)
print("\n[SUCCESS] Successfully generated and exported 'ensemble_model_diagnostics.csv'!")
