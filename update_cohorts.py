import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.matplotlib_cache')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

import generate_final_rankings as gfr

b_global = gfr.b.copy().reset_index(drop=True)
b_global['global_rank'] = range(1, len(b_global) + 1)

bw_global = gfr.bw.copy().reset_index(drop=True)
bw_global['global_rank'] = range(1, len(bw_global) + 1)

# IPL-Active cohort (ipl_balls > 0)
b_ipl = b_global[b_global['ipl_balls'] > 0].copy().reset_index(drop=True)
b_ipl['ipl_rank'] = range(1, len(b_ipl) + 1)

bw_ipl = bw_global[bw_global['ipl_balls'] > 0].copy().reset_index(drop=True)
bw_ipl['ipl_rank'] = range(1, len(bw_ipl) + 1)

# Consistency metrics for both cohorts
legal_bbb = gfr.legal_bbb

def add_consistency(df, id_col, is_batter=True):
    cons = []
    for _, r in df.iterrows():
        p_id = r[id_col]
        sub = legal_bbb[(legal_bbb[id_col] == p_id) & (legal_bbb['is_hp'] == 1)]
        if is_batter:
            m_grp = sub.groupby('match_id').agg(rae_w=('bat_rae_w', 'sum'))
            pos = (m_grp['rae_w'] > 0).sum()
        else:
            m_grp = sub.groupby('match_id').agg(rsae_w=('bowl_rsae_w', 'sum'), wkts=('is_bowler_wicket', 'sum'))
            pos = ((m_grp['rsae_w'] > 0) | (m_grp['wkts'] > 0)).sum()
        m_count = len(m_grp)
        pos_rate = pos / max(1, m_count) * 100.0
        cons.append({
            id_col: p_id,
            'hp_matches': m_count,
            'positive_hp_matches': pos,
            'positive_impact_pct': pos_rate,
            'distinct_opponents': sub['bowling_team_id' if is_batter else 'batting_team_id'].nunique(),
            'hp_inn1_balls': (sub['innings'] == 1).sum(),
            'hp_inn2_balls': (sub['innings'] == 2).sum()
        })
    return df.merge(pd.DataFrame(cons), on=id_col)

top10_b_ipl = add_consistency(b_ipl.head(10).copy(), 'striker_id', is_batter=True)
top10_bw_ipl = add_consistency(bw_ipl.head(10).copy(), 'bowler_id', is_batter=False)

top10_b_global = add_consistency(b_global.head(10).copy(), 'striker_id', is_batter=True)
top10_bw_global = add_consistency(bw_global.head(10).copy(), 'bowler_id', is_batter=False)

# Export CSVs
top10_b_ipl.to_csv('top_10_batters_ipl_active.csv', index=False)
top10_bw_ipl.to_csv('top_10_bowlers_ipl_active.csv', index=False)
top10_b_global.to_csv('top_10_batters_global.csv', index=False)
top10_bw_global.to_csv('top_10_bowlers_global.csv', index=False)

# Also save primary files for default submission
top10_b_ipl.to_csv('top_10_batters_under_pressure.csv', index=False)
top10_bw_ipl.to_csv('top_10_bowlers_under_pressure.csv', index=False)

print('Exported all CSV tables successfully.')

# Generate Updated Visualizations for IPL-Active Core
os.makedirs('visualizations', exist_ok=True)
sns.set_theme(style='whitegrid', font='sans-serif')

# Plot 1: IPL Top 10 Batters Strike Rate vs Baseline
plt.figure(figsize=(12, 6.8))
y_pos = np.arange(len(top10_b_ipl))
width = 0.38
plt.barh(y_pos - width/2, top10_b_ipl['hp_sr'], width, label='High-Pressure SR (PI ≥ 65)', color='#E03A3E', alpha=0.9)
plt.barh(y_pos + width/2, top10_b_ipl['lp_sr'], width, label='Baseline / Neutral SR', color='#1D428A', alpha=0.7)
plt.yticks(y_pos, top10_b_ipl['striker_name'] + ' (Rank ' + top10_b_ipl['ipl_rank'].astype(str) + ')')
plt.xlabel('Strike Rate (Runs per 100 Balls)', fontsize=12, fontweight='bold')
plt.title('Rajasthan Royals Primary Cohort: Top 10 Batters High-Pressure SR vs Baseline', fontsize=13, fontweight='bold', pad=15)
plt.legend(loc='lower right', frameon=True)
plt.gca().invert_yaxis()
for i, v in enumerate(top10_b_ipl['hp_sr']):
    delta = top10_b_ipl.loc[i, 'clutch_sr_delta']
    plt.text(v + 2, i - width/2 + 0.1, f'{v:.1f} (+{delta:.1f})', color='#900C3F', fontweight='bold', va='center', fontsize=9.5)
plt.tight_layout()
plt.savefig('visualizations/top_10_batters_strike_rates.png', dpi=300)
plt.close()

# Plot 2: IPL Top 10 Bowlers Economy vs Baseline
plt.figure(figsize=(12, 6.8))
y_pos = np.arange(len(top10_bw_ipl))
width = 0.38
plt.barh(y_pos - width/2, top10_bw_ipl['hp_econ'], width, label='High-Pressure Economy (PI ≥ 65)', color='#1D428A', alpha=0.9)
plt.barh(y_pos + width/2, top10_bw_ipl['lp_econ'], width, label='Baseline Economy', color='#888888', alpha=0.6)
plt.yticks(y_pos, top10_bw_ipl['bowler_name'] + ' (Rank ' + top10_bw_ipl['ipl_rank'].astype(str) + ')')
plt.xlabel('Economy Rate (Runs Conceded per Over)', fontsize=12, fontweight='bold')
plt.title('Rajasthan Royals Primary Cohort: Top 10 Bowlers High-Pressure Economy vs Baseline', fontsize=13, fontweight='bold', pad=15)
plt.legend(loc='lower right', frameon=True)
plt.gca().invert_yaxis()
for i, v in enumerate(top10_bw_ipl['hp_econ']):
    rsae = top10_bw_ipl.loc[i, 'hp_rsae6_w']
    plt.text(v + 0.15, i - width/2 + 0.1, f'{v:.2f} ({rsae:+.2f} rpo saved)', color='#0B5345', fontweight='bold', va='center', fontsize=9.5)
plt.tight_layout()
plt.savefig('visualizations/top_10_bowlers_economy.png', dpi=300)
plt.close()

print('Updated visualizations saved successfully.')

