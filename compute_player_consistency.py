import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.matplotlib_cache')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

import generate_final_rankings as gfr

legal_bbb = gfr.legal_bbb
top_b = gfr.b.head(10).copy()
top_bw = gfr.bw.head(10).copy()

# Add ranks
top_b['rank'] = range(1, 11)
top_bw['rank'] = range(1, 11)

print('Calculating match-by-match consistency...')

# Batter consistency
b_consistency = []
for _, r in top_b.iterrows():
    p_id = r['striker_id']
    sub = legal_bbb[(legal_bbb['striker_id'] == p_id) & (legal_bbb['is_hp'] == 1)]
    m_grp = sub.groupby('match_id').agg(
        balls=('runs', 'count'),
        runs=('runs', 'sum'),
        rae_w=('bat_rae_w', 'sum')
    )
    m_count = len(m_grp)
    pos_matches = (m_grp['rae_w'] > 0).sum()
    pos_rate = pos_matches / max(1, m_count) * 100.0
    opp_count = sub['bowling_team_id'].nunique()
    inn1_balls = (sub['innings'] == 1).sum()
    inn2_balls = (sub['innings'] == 2).sum()
    b_consistency.append({
        'striker_id': p_id,
        'hp_matches': m_count,
        'positive_hp_matches': pos_matches,
        'positive_impact_pct': pos_rate,
        'distinct_opponents': opp_count,
        'hp_inn1_balls': inn1_balls,
        'hp_inn2_balls': inn2_balls
    })

top_b = top_b.merge(pd.DataFrame(b_consistency), on='striker_id')

# Bowler consistency
bw_consistency = []
for _, r in top_bw.iterrows():
    p_id = r['bowler_id']
    sub = legal_bbb[(legal_bbb['bowler_id'] == p_id) & (legal_bbb['is_hp'] == 1)]
    m_grp = sub.groupby('match_id').agg(
        balls=('is_legal', 'count'),
        runs=('bowler_runs', 'sum'),
        wkts=('is_bowler_wicket', 'sum'),
        rsae_w=('bowl_rsae_w', 'sum')
    )
    m_count = len(m_grp)
    pos_matches = ((m_grp['rsae_w'] > 0) | (m_grp['wkts'] > 0)).sum()
    pos_rate = pos_matches / max(1, m_count) * 100.0
    opp_count = sub['batting_team_id'].nunique()
    inn1_balls = (sub['innings'] == 1).sum()
    inn2_balls = (sub['innings'] == 2).sum()
    bw_consistency.append({
        'bowler_id': p_id,
        'hp_matches': m_count,
        'positive_hp_matches': pos_matches,
        'positive_impact_pct': pos_rate,
        'distinct_opponents': opp_count,
        'hp_inn1_balls': inn1_balls,
        'hp_inn2_balls': inn2_balls
    })

top_bw = top_bw.merge(pd.DataFrame(bw_consistency), on='bowler_id')

# Save official rankings to CSV
top_b.to_csv('top_10_batters_under_pressure.csv', index=False)
top_bw.to_csv('top_10_bowlers_under_pressure.csv', index=False)
print('Saved top_10_batters_under_pressure.csv and top_10_bowlers_under_pressure.csv')

# Generate Visualizations
os.makedirs('visualizations', exist_ok=True)
sns.set_theme(style='whitegrid', font='sans-serif')

# Plot 1: Top 10 Batters - Pressure Strike Rate vs Baseline Strike Rate (Clutch Delta)
plt.figure(figsize=(12, 7))
y_pos = np.arange(len(top_b))
width = 0.38
plt.barh(y_pos - width/2, top_b['hp_sr'], width, label='High-Pressure SR (PI ≥ 65)', color='#E03A3E', alpha=0.9)
plt.barh(y_pos + width/2, top_b['lp_sr'], width, label='Baseline / Neutral SR', color='#1D428A', alpha=0.7)
plt.yticks(y_pos, top_b['striker_name'] + ' (Rank ' + top_b['rank'].astype(str) + ')')
plt.xlabel('Strike Rate (Runs per 100 Balls)', fontsize=12, fontweight='bold')
plt.title('Top 10 Batters: High-Pressure Strike Rate vs Baseline Platform', fontsize=14, fontweight='bold', pad=15)
plt.legend(loc='lower right', frameon=True)
plt.gca().invert_yaxis()
for i, v in enumerate(top_b['hp_sr']):
    delta = top_b.loc[i, 'clutch_sr_delta']
    plt.text(v + 2, i - width/2 + 0.1, f'{v:.1f} (+{delta:.1f})', color='#900C3F', fontweight='bold', va='center')
plt.tight_layout()
plt.savefig('visualizations/top_10_batters_strike_rates.png', dpi=300)
plt.close()

# Plot 2: Top 10 Bowlers - Economy Suppression & Runs Saved
plt.figure(figsize=(12, 7))
y_pos = np.arange(len(top_bw))
width = 0.38
plt.barh(y_pos - width/2, top_bw['hp_econ'], width, label='High-Pressure Economy (PI ≥ 65)', color='#1D428A', alpha=0.9)
plt.barh(y_pos + width/2, top_bw['lp_econ'], width, label='Baseline Economy', color='#888888', alpha=0.6)
plt.yticks(y_pos, top_bw['bowler_name'] + ' (Rank ' + top_bw['rank'].astype(str) + ')')
plt.xlabel('Economy Rate (Runs Conceded per Over)', fontsize=12, fontweight='bold')
plt.title('Top 10 Bowlers: High-Pressure Economy Suppression vs Baseline', fontsize=14, fontweight='bold', pad=15)
plt.legend(loc='lower right', frameon=True)
plt.gca().invert_yaxis()
for i, v in enumerate(top_bw['hp_econ']):
    rsae = top_bw.loc[i, 'hp_rsae6_w']
    plt.text(v + 0.15, i - width/2 + 0.1, f'{v:.2f} ({rsae:+.2f} rpo saved)', color='#0B5345', fontweight='bold', va='center')
plt.tight_layout()
plt.savefig('visualizations/top_10_bowlers_economy.png', dpi=300)
plt.close()

# Plot 3: Pressure Index Distribution
plt.figure(figsize=(10, 5))
sns.histplot(gfr.legal_bbb['pressure_index'], bins=40, kde=True, color='#E03A3E')
plt.axvline(65, color='#1D428A', linestyle='--', linewidth=2, label='High-Pressure Cutoff (PI ≥ 65, 75th percentile)')
plt.title('Distribution of Rajasthan Royals Delivery-Level Pressure Index (RR-PI)', fontsize=13, fontweight='bold')
plt.xlabel('Pressure Index (0 - 100 Scale)', fontsize=11, fontweight='bold')
plt.ylabel('Delivery Count', fontsize=11, fontweight='bold')
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig('visualizations/pressure_index_distribution.png', dpi=300)
plt.close()

print('Visualizations generated successfully in visualizations/ directory!')
print('\nFinal Top 10 Batters with consistency:')
print(top_b[['rank', 'striker_name', 'hp_balls', 'hp_sr', 'clutch_sr_delta', 'hp_avg', 'positive_impact_pct', 'rating']].to_string(index=False))
print('\nFinal Top 10 Bowlers with consistency:')
print(top_bw[['rank', 'bowler_name', 'hp_balls', 'hp_econ', 'hp_sr', 'hp_rsae6_w', 'positive_impact_pct', 'rating']].to_string(index=False))

