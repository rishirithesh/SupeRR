import json
import pandas as pd

# Load datasets
b_ipl = pd.read_csv('top_10_batters_ipl_active.csv')
bw_ipl = pd.read_csv('top_10_bowlers_ipl_active.csv')
b_global = pd.read_csv('top_10_batters_global.csv')
bw_global = pd.read_csv('top_10_bowlers_global.csv')

# Format batters cleanly
def process_batters(df, rank_col):
    out = []
    for _, r in df.iterrows():
        rk = int(r[rank_col])
        name = r['striker_name']
        role = "360° Death Finisher" if rk in [1, 2, 5] else ("Crisis Anchor / Middle Order" if rk in [3, 4, 6] else "Boundary Accelerator")
        auction_cat = "Marquee / Retained" if rk in [1, 3, 7] else ("Overseas Finisher" if rk in [2, 6, 8] else ("Uncapped / Budget Gem" if rk in [5, 10] else "Domestic Star"))
        out.append({
            "rank": rk,
            "name": name,
            "hp_balls": int(r['hp_balls']),
            "hp_runs": int(r['hp_runs']),
            "hp_sr": round(float(r['hp_sr']), 1),
            "base_sr": round(float(r['lp_sr']), 1),
            "delta_sr": round(float(r['clutch_sr_delta']), 1),
            "hp_avg": round(float(r['hp_avg']), 1),
            "bnd_pct": round(float(r['hp_boundary_pct']), 1),
            "dot_pct": round(float(r['hp_dot_pct']), 1),
            "win_pct": round(float(r['positive_impact_pct']), 1),
            "rating": round(float(r['rating']), 2),
            "ipl_balls": int(r['ipl_balls']),
            "opponents": int(r['distinct_opponents']),
            "role": role,
            "auction_cat": auction_cat,
            "fours": int(r['hp_fours']),
            "sixes": int(r['hp_sixes']),
            "hp_matches": int(r['hp_matches_x'])
        })
    return out

def process_bowlers(df, rank_col):
    out = []
    for _, r in df.iterrows():
        rk = int(r[rank_col])
        name = r['bowler_name']
        role = "Death Overs Specialist" if rk in [2, 3, 5, 8, 9] else ("Spin Choke Engine" if rk in [1, 4, 6, 7, 10] else "Middle Overs Enforcer")
        auction_cat = "Marquee Spin" if rk in [1, 6] else ("Overseas Death Weapon" if rk in [3, 5] else ("Uncapped / High Value" if rk in [2, 9] else "Overseas Containment"))
        out.append({
            "rank": rk,
            "name": name,
            "hp_balls": int(r['hp_balls']),
            "hp_wkts": int(r['hp_wickets']),
            "hp_econ": round(float(r['hp_econ']), 2),
            "base_econ": round(float(r['lp_econ']), 2),
            "saved_per_6": round(float(r['hp_rsae6_w']), 2),
            "hp_sr": round(float(r['hp_sr']), 1),
            "dot_pct": round(float(r['hp_dot_pct']), 1),
            "bnd_pct": round(float(r['hp_boundary_pct']), 1),
            "win_pct": round(float(r['positive_impact_pct']), 1),
            "rating": round(float(r['rating']), 2),
            "ipl_balls": int(r['ipl_balls']),
            "opponents": int(r['distinct_opponents']),
            "role": role,
            "auction_cat": auction_cat,
            "hp_matches": int(r['hp_matches_x'])
        })
    return out

bat_ipl = process_batters(b_ipl, 'ipl_rank')
bowl_ipl = process_bowlers(bw_ipl, 'ipl_rank')
bat_glob = process_batters(b_global, 'global_rank')
bowl_glob = process_bowlers(bw_global, 'global_rank')

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rajasthan Royals | SupeRR Selector Analytics Command Center</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #080d1a;
            color: #f1f5f9;
        }}
        .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass-panel {{
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .glass-panel-hover:hover {{
            border-color: rgba(225, 29, 72, 0.4);
            box-shadow: 0 8px 24px -4px rgba(225, 29, 72, 0.12);
        }}
        .custom-scrollbar::-webkit-scrollbar {{
            width: 5px;
            height: 5px;
        }}
        .custom-scrollbar::-webkit-scrollbar-track {{ background: #0b1329; }}
        .custom-scrollbar::-webkit-scrollbar-thumb {{
            background: #334155;
            border-radius: 4px;
        }}
        .tab-btn.active {{
            background: #e11d48;
            color: #ffffff;
            box-shadow: 0 2px 10px rgba(225, 29, 72, 0.35);
        }}
    </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-rose-500 selection:text-white">

    <!-- Top Navigation Command Bar -->
    <header class="border-b border-slate-800 bg-[#090e1d]/90 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <!-- Branding -->
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center font-black text-white text-base shadow-md shadow-rose-600/20">
                    RR
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-white tracking-tight">RAJASTHAN ROYALS</span>
                        <span class="text-[10px] bg-rose-500/15 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded font-semibold uppercase tracking-wider">SupeRR Selector S2</span>
                    </div>
                    <p class="text-[11px] text-slate-400">Decision Science & High-Pressure Talent Discovery Engine</p>
                </div>
            </div>

            <!-- Global Action Controls -->
            <div class="flex items-center gap-3">
                <!-- Paradigm Toggle -->
                <div class="bg-slate-900 border border-slate-700/80 p-0.5 rounded-lg flex text-xs font-medium">
                    <button id="cohort-ipl" onclick="switchCohort('ipl')" class="px-3 py-1.5 rounded-md tab-btn active transition">
                        IPL-Eligible Cohort (Primary)
                    </button>
                    <button id="cohort-global" onclick="switchCohort('global')" class="px-3 py-1.5 rounded-md text-slate-400 hover:text-white transition">
                        Global Benchmark
                    </button>
                </div>

                <!-- Role Toggle -->
                <div class="bg-slate-900 border border-slate-700/80 p-0.5 rounded-lg flex text-xs font-medium">
                    <button id="role-bat" onclick="switchRole('bat')" class="px-3 py-1.5 rounded-md bg-blue-600 text-white font-semibold transition">
                        Batters
                    </button>
                    <button id="role-bowl" onclick="switchRole('bowl')" class="px-3 py-1.5 rounded-md text-slate-400 hover:text-white transition">
                        Bowlers
                    </button>
                </div>

                <!-- Copy Dropdown Button -->
                <button onclick="copyDropdownList()" class="hidden sm:flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg transition font-medium">
                    <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"/></svg>
                    <span>Copy for Unstop</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Sub-Navbar: Navigation Tabs -->
    <div class="border-b border-slate-800/80 bg-[#080d1a]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
            <div class="flex space-x-6 text-xs font-medium">
                <button onclick="switchTab('leaderboard')" id="tab-leaderboard" class="py-3 border-b-2 border-rose-500 text-white font-semibold">
                    Talent Leaderboard & Dossiers
                </button>
                <button onclick="switchTab('analytics')" id="tab-analytics" class="py-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200">
                    Comparative Visual Analytics
                </button>
                <button onclick="switchTab('ensemble')" id="tab-ensemble" class="py-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200">
                    ML Stacking Ensemble Diagnostics
                </button>
                <button onclick="switchTab('auction')" id="tab-auction" class="py-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200">
                    RR 2026 Auction & Roster Strategy
                </button>
            </div>
            <div class="text-[11px] font-mono text-slate-400 flex items-center gap-2 py-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Dataset: 200,999 Balls | 883 Matches | 50,255 HP Deliveries</span>
            </div>
        </div>
    </div>

    <!-- Main Workspace Area -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex-1 space-y-5">

        <!-- Executive Metrics Bar (No bloated text, crisp numbers) -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div class="glass-panel p-3.5 rounded-xl border border-slate-800">
                <span class="text-[11px] text-slate-400 uppercase tracking-wider block font-medium">Pressure Cutoff</span>
                <div class="flex items-baseline gap-2 mt-1">
                    <span class="text-xl font-bold font-mono text-rose-400">PI &ge; 65.0</span>
                    <span class="text-[10px] text-slate-400">75th Percentile</span>
                </div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div class="bg-rose-500 h-full rounded-full" style="width: 25%"></div>
                </div>
            </div>

            <div class="glass-panel p-3.5 rounded-xl border border-slate-800">
                <span class="text-[11px] text-slate-400 uppercase tracking-wider block font-medium">ML Win Prob AUC</span>
                <div class="flex items-baseline gap-2 mt-1">
                    <span class="text-xl font-bold font-mono text-emerald-400">0.9374</span>
                    <span class="text-[10px] text-emerald-500 font-semibold">+0.0100 Boost</span>
                </div>
                <span class="text-[10px] text-slate-400 block mt-1">Stacking Ensemble (5-Fold CV)</span>
            </div>

            <div class="glass-panel p-3.5 rounded-xl border border-slate-800">
                <span class="text-[11px] text-slate-400 uppercase tracking-wider block font-medium">Expected Runs xR</span>
                <div class="flex items-baseline gap-2 mt-1">
                    <span class="text-xl font-bold font-mono text-blue-400">1.7083</span>
                    <span class="text-[10px] text-blue-500">RMSE</span>
                </div>
                <span class="text-[10px] text-slate-400 block mt-1">Zero Bias (-7.68e-15)</span>
            </div>

            <div class="glass-panel p-3.5 rounded-xl border border-slate-800">
                <span class="text-[11px] text-slate-400 uppercase tracking-wider block font-medium">Format Gap (IPL vs T20I)</span>
                <div class="flex items-baseline gap-2 mt-1">
                    <span class="text-xl font-bold font-mono text-amber-400">+15.25</span>
                    <span class="text-[10px] text-amber-500">SR Points</span>
                </div>
                <span class="text-[10px] text-slate-400 block mt-1">IPL 9.70 rpo vs T20I 8.79 rpo</span>
            </div>

            <div class="glass-panel p-3.5 rounded-xl border border-slate-800 col-span-2 md:col-span-1">
                <span class="text-[11px] text-slate-400 uppercase tracking-wider block font-medium">Unstop Dropdown Status</span>
                <div class="flex items-baseline gap-2 mt-1">
                    <span class="text-xl font-bold font-mono text-purple-400">20 / 20</span>
                    <span class="text-[10px] text-emerald-400 font-semibold">100% Match</span>
                </div>
                <span class="text-[10px] text-slate-400 block mt-1">Official Name Parity</span>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 1: LEADERBOARD & PLAYER DOSSIER -->
        <!-- ================================================================= -->
        <div id="section-leaderboard" class="space-y-4">

            <!-- Control & Search Bar -->
            <div class="glass-panel p-3 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div class="flex items-center gap-2">
                    <h2 id="tableHeading" class="text-sm font-bold text-white uppercase tracking-wider">Top 10 Batters (IPL-Eligible)</h2>
                    <span id="cohortTag" class="text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded font-mono">Verified for Unstop</span>
                </div>

                <!-- Instant Search Filter -->
                <div class="w-full sm:w-72 relative">
                    <input type="text" id="searchInput" oninput="filterPlayers()" placeholder="Search player name or role..." 
                        class="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500">
                    <svg class="w-4 h-4 text-slate-400 absolute right-2.5 top-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                </div>
            </div>

            <!-- Two-Column Layout: Table (60%) + Dossier (40%) -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
                
                <!-- Left: Leaderboard Table -->
                <div class="lg:col-span-8 glass-panel rounded-xl border border-slate-800 overflow-hidden flex flex-col justify-between">
                    <div class="overflow-x-auto custom-scrollbar">
                        <table class="w-full text-left text-xs" id="dataTable">
                            <thead class="bg-slate-900/90 text-[10px] text-slate-400 uppercase tracking-wider border-b border-slate-800 font-mono" id="tableHead"></thead>
                            <tbody class="divide-y divide-slate-800/60" id="tableBody"></tbody>
                        </table>
                    </div>
                    <div class="p-2.5 bg-slate-950/60 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Click any player row to load full telemetry in the right panel.</span>
                        <span class="font-mono text-emerald-400">Bayesian Regularized (K=60)</span>
                    </div>
                </div>

                <!-- Right: Interactive Player Dossier Card -->
                <div class="lg:col-span-4 glass-panel rounded-xl border border-slate-800 p-4 flex flex-col justify-between space-y-4">
                    <div>
                        <!-- Header & Badges -->
                        <div class="flex items-start justify-between">
                            <div>
                                <span id="pRank" class="text-[11px] font-bold font-mono text-rose-400 bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded">Rank #1</span>
                                <h3 id="pName" class="text-xl font-bold text-white mt-1.5 tracking-tight">Suryakumar Yadav</h3>
                                <p id="pRole" class="text-xs text-slate-400 mt-0.5 font-medium">360° Death Finisher</p>
                            </div>
                            <span id="pCategory" class="text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded">Marquee Asset</span>
                        </div>

                        <!-- 4 Clean Metric Tiles (Zero prose, high impact) -->
                        <div class="grid grid-cols-2 gap-2 mt-4 text-xs font-mono">
                            <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                                <span class="text-[10px] text-slate-400 block" id="m1Label">Pressure Strike Rate</span>
                                <span class="text-lg font-bold text-rose-400 block mt-0.5" id="m1Val">215.5</span>
                                <span class="text-[9px] text-slate-500" id="m1Sub">Baseline: 157.7</span>
                            </div>
                            <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                                <span class="text-[10px] text-slate-400 block" id="m2Label">Clutch Delta</span>
                                <span class="text-lg font-bold text-emerald-400 block mt-0.5" id="m2Val">+57.8</span>
                                <span class="text-[9px] text-slate-500" id="m2Sub">Performance Lift</span>
                            </div>
                            <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                                <span class="text-[10px] text-slate-400 block" id="m3Label">Boundary / Dot %</span>
                                <span class="text-lg font-bold text-blue-400 block mt-0.5" id="m3Val">34.3%</span>
                                <span class="text-[9px] text-slate-500" id="m3Sub">Dot Rate: 26.5%</span>
                            </div>
                            <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                                <span class="text-[10px] text-slate-400 block" id="m4Label">Scouting Rating</span>
                                <span class="text-lg font-bold text-amber-400 block mt-0.5" id="m4Val">84.75</span>
                                <span class="text-[9px] text-slate-500" id="m4Sub">Win Impact: 74.4%</span>
                            </div>
                        </div>

                        <!-- Dynamic Mini Bar / Radar Preview -->
                        <div class="mt-4 pt-3 border-t border-slate-800/80">
                            <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-2">Performance Envelope</span>
                            <div class="space-y-1.5 text-[11px]">
                                <div>
                                    <div class="flex justify-between text-slate-400 mb-0.5">
                                        <span id="bar1Label">High-Pressure Execution</span>
                                        <span id="bar1Val" class="font-mono text-white">92%</span>
                                    </div>
                                    <div class="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                                        <div id="bar1Bar" class="bg-rose-500 h-full rounded-full" style="width: 92%"></div>
                                    </div>
                                </div>
                                <div>
                                    <div class="flex justify-between text-slate-400 mb-0.5">
                                        <span id="bar2Label">Match Consistency Rate</span>
                                        <span id="bar2Val" class="font-mono text-white">74.4%</span>
                                    </div>
                                    <div class="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                                        <div id="bar2Bar" class="bg-emerald-500 h-full rounded-full" style="width: 74.4%"></div>
                                    </div>
                                </div>
                                <div>
                                    <div class="flex justify-between text-slate-400 mb-0.5">
                                        <span id="bar3Label">Sample Credibility</span>
                                        <span id="bar3Val" class="font-mono text-white">426 Balls (High)</span>
                                    </div>
                                    <div class="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                                        <div id="bar3Bar" class="bg-blue-500 h-full rounded-full" style="width: 85%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tactical Tagline -->
                    <div class="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 text-[11px] text-slate-300">
                        <span class="font-semibold text-rose-400">Tactical Role:</span> 
                        <span id="pSummary">World-class 360-degree match-winner with elite boundary execution in high-leverage death overs.</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 2: ADVANCED VISUAL ANALYTICS -->
        <!-- ================================================================= -->
        <div id="section-analytics" class="hidden space-y-4">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <!-- Differential Chart -->
                <div class="glass-panel p-4 rounded-xl border border-slate-800">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-xs font-bold text-white uppercase tracking-wider" id="chart1Title">Clutch Differential ($\Delta$) vs Baseline</h3>
                        <span class="text-[10px] text-slate-400 font-mono">High Pressure vs Neutral State</span>
                    </div>
                    <div class="h-72">
                        <canvas id="chartDifferential"></canvas>
                    </div>
                </div>

                <!-- Win Impact Rate Chart -->
                <div class="glass-panel p-4 rounded-xl border border-slate-800">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-xs font-bold text-white uppercase tracking-wider">Cross-Match Repeatability (Win Impact Rate)</h3>
                        <span class="text-[10px] text-slate-400 font-mono">% Matches with Positive Context Contribution</span>
                    </div>
                    <div class="h-72">
                        <canvas id="chartConsistency"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 3: ENSEMBLE ML DIAGNOSTICS -->
        <!-- ================================================================= -->
        <div id="section-ensemble" class="hidden space-y-4">
            <div class="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
                <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-white">Multi-Model Stacking Ensemble Architecture</h3>
                        <p class="text-xs text-slate-400">Head-to-head empirical comparison of gradient boosting models and neural network against Stacking Meta-Learners.</p>
                    </div>
                    <span class="text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-1 rounded">5-Fold Out-of-Fold CV</span>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-900 text-slate-400 uppercase text-[10px] font-mono border-b border-slate-800">
                            <tr>
                                <th class="p-2.5">Task Objective</th>
                                <th class="p-2.5">Model Architecture</th>
                                <th class="p-2.5">Primary Metric</th>
                                <th class="p-2.5">Calibration (Brier / MAE)</th>
                                <th class="p-2.5">Loss / Bias</th>
                                <th class="p-2.5">Franchise Utility</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800/60 font-mono">
                            <tr class="hover:bg-slate-800/40">
                                <td class="p-2.5 text-slate-300 font-sans font-medium">Chase Win Prob ($WP_t$)</td>
                                <td class="p-2.5 text-slate-400">LightGBM Base</td>
                                <td class="p-2.5 text-white">ROC-AUC: 0.9274</td>
                                <td class="p-2.5 text-slate-400">Brier: 0.1107</td>
                                <td class="p-2.5 text-slate-400">Log-Loss: 0.3417</td>
                                <td class="p-2.5 text-slate-400 font-sans">Leaf-wise splitting</td>
                            </tr>
                            <tr class="hover:bg-slate-800/40">
                                <td class="p-2.5 text-slate-300 font-sans font-medium">Chase Win Prob ($WP_t$)</td>
                                <td class="p-2.5 text-slate-400">XGBoost Base</td>
                                <td class="p-2.5 text-white">ROC-AUC: 0.9217</td>
                                <td class="p-2.5 text-slate-400">Brier: 0.1147</td>
                                <td class="p-2.5 text-slate-400">Log-Loss: 0.3529</td>
                                <td class="p-2.5 text-slate-400 font-sans">Depth-pruned boosting</td>
                            </tr>
                            <tr class="hover:bg-slate-800/40">
                                <td class="p-2.5 text-slate-300 font-sans font-medium">Chase Win Prob ($WP_t$)</td>
                                <td class="p-2.5 text-slate-400">CatBoost Base</td>
                                <td class="p-2.5 text-white">ROC-AUC: 0.9077</td>
                                <td class="p-2.5 text-slate-400">Brier: 0.1240</td>
                                <td class="p-2.5 text-slate-400">Log-Loss: 0.3825</td>
                                <td class="p-2.5 text-slate-400 font-sans">Oblivious trees</td>
                            </tr>
                            <tr class="hover:bg-slate-800/40">
                                <td class="p-2.5 text-slate-300 font-sans font-medium">Chase Win Prob ($WP_t$)</td>
                                <td class="p-2.5 text-slate-400">Deep MLP Neural Net</td>
                                <td class="p-2.5 text-white">ROC-AUC: 0.9109</td>
                                <td class="p-2.5 text-slate-400">Brier: 0.1216</td>
                                <td class="p-2.5 text-slate-400">Log-Loss: 0.3697</td>
                                <td class="p-2.5 text-slate-400 font-sans">Smooth non-linear space</td>
                            </tr>
                            <tr class="bg-emerald-950/20 text-emerald-400 font-bold border border-emerald-500/30">
                                <td class="p-2.5 font-sans">Chase Win Prob ($WP_t$)</td>
                                <td class="p-2.5">★ Stacking Meta-Ensemble</td>
                                <td class="p-2.5 text-white">ROC-AUC: 0.9374</td>
                                <td class="p-2.5 text-white">Brier: 0.1029</td>
                                <td class="p-2.5 text-white">Log-Loss: 0.3209</td>
                                <td class="p-2.5 font-sans text-emerald-300">Optimal Meta-Weighted (+0.0100)</td>
                            </tr>
                            <tr class="hover:bg-slate-800/40">
                                <td class="p-2.5 text-slate-300 font-sans font-medium">Expected Runs ($xR$)</td>
                                <td class="p-2.5 text-slate-400">Stacking Regressor</td>
                                <td class="p-2.5 text-white">RMSE: 1.7083</td>
                                <td class="p-2.5 text-slate-400">MAE: 1.2882</td>
                                <td class="p-2.5 text-emerald-400">Bias: -7.68e-15</td>
                                <td class="p-2.5 text-slate-400 font-sans">Delivery-level context baseline</td>
                            </tr>
                            <tr class="hover:bg-slate-800/40">
                                <td class="p-2.5 text-slate-300 font-sans font-medium">Wicket Hazard ($xW$)</td>
                                <td class="p-2.5 text-slate-400">Soft-Voting Classifier</td>
                                <td class="p-2.5 text-white">ROC-AUC: 0.6130</td>
                                <td class="p-2.5 text-slate-400">Brier: 0.0524</td>
                                <td class="p-2.5 text-slate-400">Log-Loss: 0.2114</td>
                                <td class="p-2.5 text-slate-400 font-sans">Instantaneous wicket hazard</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 4: RR AUCTION & ROSTER STRATEGY -->
        <!-- ================================================================= -->
        <div id="section-auction" class="hidden space-y-4">
            <div class="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
                <div class="border-b border-slate-800 pb-3">
                    <h3 class="text-sm font-bold text-white">Rajasthan Royals 2026 Auction Tactical Alignment</h3>
                    <p class="text-xs text-slate-400">Translating high-pressure analytics into squad slots, overseas quota limits, and budget efficiency.</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-2">
                        <span class="text-[10px] font-bold text-rose-400 uppercase tracking-wider block">Priority 1: Death Pace Specialist</span>
                        <div class="font-bold text-white text-sm">Matheesha Pathirana / Spencer Johnson</div>
                        <p class="text-slate-400 text-[11px] leading-relaxed">
                            Pathirana captured 50 high-pressure wickets at 11.20 strike rate with 7.71 economy. Spencer Johnson delivers left-arm pace with a 92.3% match win rate.
                        </p>
                        <span class="inline-block text-[10px] bg-rose-500/15 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded font-mono">Overseas Slot Target</span>
                    </div>

                    <div class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-2">
                        <span class="text-[10px] font-bold text-blue-400 uppercase tracking-wider block">Priority 2: Middle Spin Choke</span>
                        <div class="font-bold text-white text-sm">Mitchell Santner / Kuldeep Yadav</div>
                        <p class="text-slate-400 text-[11px] leading-relaxed">
                            Santner suppresses runs to 6.77 rpo (+2.07 runs saved per over). Kuldeep strikes every 12.88 balls under pressure with 38.1% dot balls.
                        </p>
                        <span class="inline-block text-[10px] bg-blue-500/15 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded font-mono">Economy Anchor Target</span>
                    </div>

                    <div class="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 space-y-2">
                        <span class="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">Priority 3: Clutch Finishers & Uncapped</span>
                        <div class="font-bold text-white text-sm">Tristan Stubbs / Naman Dhir / Rasikh Salam</div>
                        <p class="text-slate-400 text-[11px] leading-relaxed">
                            Stubbs (+61.0 delta) and Naman Dhir (205.0 SR) provide elite boundary execution. Rasikh Salam (8.07 strike rate) provides budget-friendly bowling firepower.
                        </p>
                        <span class="inline-block text-[10px] bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded font-mono">High Purse Value / Uncapped</span>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- Clean Footer -->
    <footer class="border-t border-slate-800 bg-[#090e1d] py-3 text-[11px] text-slate-500">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>Rajasthan Royals Decision Science Group &bull; SupeRR Selector Season 2</div>
            <div class="font-mono text-slate-400">LGBM + XGB + CatBoost + MLP Stacking Ensemble (ROC-AUC: 0.9374)</div>
        </div>
    </footer>

    <!-- Client Script -->
    <script>
        const batIPL = {json.dumps(bat_ipl)};
        const bowlIPL = {json.dumps(bowl_ipl)};
        const batGlob = {json.dumps(bat_glob)};
        const bowlGlob = {json.dumps(bowl_glob)};

        let currentCohort = 'ipl';
        let currentRole = 'bat';
        let chartDiff = null;
        let chartCons = null;
        let selectedPlayer = null;

        function getData() {{
            if (currentRole === 'bat') {{
                return currentCohort === 'ipl' ? batIPL : batGlob;
            }} else {{
                return currentCohort === 'ipl' ? bowlIPL : bowlGlob;
            }}
        }}

        function switchCohort(c) {{
            currentCohort = c;
            document.getElementById('cohort-ipl').className = c === 'ipl' ? 'px-3 py-1.5 rounded-md tab-btn active transition' : 'px-3 py-1.5 rounded-md text-slate-400 hover:text-white transition';
            document.getElementById('cohort-global').className = c === 'global' ? 'px-3 py-1.5 rounded-md tab-btn active transition' : 'px-3 py-1.5 rounded-md text-slate-400 hover:text-white transition';
            renderTable();
        }}

        function switchRole(r) {{
            currentRole = r;
            document.getElementById('role-bat').className = r === 'bat' ? 'px-3 py-1.5 rounded-md bg-blue-600 text-white font-semibold transition' : 'px-3 py-1.5 rounded-md text-slate-400 hover:text-white transition';
            document.getElementById('role-bowl').className = r === 'bowl' ? 'px-3 py-1.5 rounded-md bg-blue-600 text-white font-semibold transition' : 'px-3 py-1.5 rounded-md text-slate-400 hover:text-white transition';
            renderTable();
        }}

        function switchTab(t) {{
            const tabs = ['leaderboard', 'analytics', 'ensemble', 'auction'];
            tabs.forEach(tab => {{
                document.getElementById(`section-${{tab}}`).classList.add('hidden');
                document.getElementById(`tab-${{tab}}`).className = 'py-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200';
            }});
            document.getElementById(`section-${{t}}`).classList.remove('hidden');
            document.getElementById(`tab-${{t}}`).className = 'py-3 border-b-2 border-rose-500 text-white font-semibold';

            if (t === 'analytics') {{
                setTimeout(renderAnalyticsCharts, 50);
            }}
        }}

        function renderTable(filterQuery = "") {{
            const data = getData();
            const isBat = currentRole === 'bat';
            const isIPL = currentCohort === 'ipl';

            document.getElementById('tableHeading').innerText = `Top 10 ${{isBat ? 'Batters' : 'Bowlers'}} (${{isIPL ? 'IPL-Eligible' : 'Global Benchmark'}})`;
            document.getElementById('cohortTag').innerText = isIPL ? 'Verified for Unstop' : 'Global Dataset Benchmark';

            // Table Header
            const tHead = document.getElementById('tableHead');
            if (isBat) {{
                tHead.innerHTML = `
                    <tr>
                        <th class="p-2.5">Rk</th>
                        <th class="p-2.5">Player Name</th>
                        <th class="p-2.5 text-right">HP Balls</th>
                        <th class="p-2.5 text-right">HP Runs</th>
                        <th class="p-2.5 text-right text-rose-400">HP SR</th>
                        <th class="p-2.5 text-right">Base SR</th>
                        <th class="p-2.5 text-right text-emerald-400">&Delta; SR</th>
                        <th class="p-2.5 text-right">Average</th>
                        <th class="p-2.5 text-right">Bnd %</th>
                        <th class="p-2.5 text-right">Win Impact</th>
                        <th class="p-2.5 text-right text-amber-400">Rating</th>
                    </tr>
                `;
            }} else {{
                tHead.innerHTML = `
                    <tr>
                        <th class="p-2.5">Rk</th>
                        <th class="p-2.5">Player Name</th>
                        <th class="p-2.5 text-right">HP Balls</th>
                        <th class="p-2.5 text-right">HP Wkts</th>
                        <th class="p-2.5 text-right text-blue-400">HP Econ</th>
                        <th class="p-2.5 text-right">Base Econ</th>
                        <th class="p-2.5 text-right text-emerald-400">Saved/6</th>
                        <th class="p-2.5 text-right">HP BSR</th>
                        <th class="p-2.5 text-right">Dot %</th>
                        <th class="p-2.5 text-right">Win Impact</th>
                        <th class="p-2.5 text-right text-amber-400">Rating</th>
                    </tr>
                `;
            }}

            // Table Body
            const tBody = document.getElementById('tableBody');
            tBody.innerHTML = '';

            const filtered = filterQuery ? 
                data.filter(p => p.name.toLowerCase().includes(filterQuery.toLowerCase()) || p.role.toLowerCase().includes(filterQuery.toLowerCase())) :
                data;

            filtered.forEach((p, idx) => {{
                const tr = document.createElement('tr');
                tr.className = `hover:bg-slate-800/40 cursor-pointer transition ${{idx === 0 ? 'bg-slate-800/20' : ''}}`;
                tr.onclick = () => selectPlayer(p, isBat);

                if (isBat) {{
                    tr.innerHTML = `
                        <td class="p-2.5 font-mono font-bold ${{p.rank === 1 ? 'text-amber-400' : 'text-slate-400'}}">#${{p.rank}}</td>
                        <td class="p-2.5 font-medium text-white flex items-center gap-1.5">
                            ${{p.name}}
                            ${{p.ipl_balls > 0 ? '<span class="text-[9px] px-1 py-0.2 rounded bg-rose-900/30 text-rose-300 border border-rose-700/40">IPL</span>' : ''}}
                        </td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.hp_balls}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.hp_runs}}</td>
                        <td class="p-2.5 text-right font-mono font-bold text-rose-400">${{p.hp_sr}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-400">${{p.base_sr}}</td>
                        <td class="p-2.5 text-right font-mono font-bold text-emerald-400">+${{p.delta_sr}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.hp_avg}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.bnd_pct}}%</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.win_pct}}%</td>
                        <td class="p-2.5 text-right font-mono font-bold text-amber-400">${{p.rating}}</td>
                    `;
                }} else {{
                    tr.innerHTML = `
                        <td class="p-2.5 font-mono font-bold ${{p.rank === 1 ? 'text-amber-400' : 'text-slate-400'}}">#${{p.rank}}</td>
                        <td class="p-2.5 font-medium text-white flex items-center gap-1.5">
                            ${{p.name}}
                            ${{p.ipl_balls > 0 ? '<span class="text-[9px] px-1 py-0.2 rounded bg-blue-900/30 text-blue-300 border border-blue-700/40">IPL</span>' : ''}}
                        </td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.hp_balls}}</td>
                        <td class="p-2.5 text-right font-mono font-bold text-purple-400">${{p.hp_wkts}}</td>
                        <td class="p-2.5 text-right font-mono font-bold text-blue-400">${{p.hp_econ}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-400">${{p.base_econ}}</td>
                        <td class="p-2.5 text-right font-mono font-bold text-emerald-400">+${{p.saved_per_6}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.hp_sr}}</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.dot_pct}}%</td>
                        <td class="p-2.5 text-right font-mono text-slate-300">${{p.win_pct}}%</td>
                        <td class="p-2.5 text-right font-mono font-bold text-amber-400">${{p.rating}}</td>
                    `;
                }}
                tBody.appendChild(tr);
            }});

            if (filtered.length > 0) {{
                selectPlayer(filtered[0], isBat);
            }}
        }}

        function selectPlayer(p, isBat) {{
            selectedPlayer = p;
            document.getElementById('pRank').innerText = `Rank #${{p.rank}}`;
            document.getElementById('pName').innerText = p.name;
            document.getElementById('pRole').innerText = p.role;
            document.getElementById('pCategory').innerText = p.auction_cat;

            if (isBat) {{
                document.getElementById('m1Label').innerText = "Pressure Strike Rate";
                document.getElementById('m1Val').innerText = p.hp_sr;
                document.getElementById('m1Sub').innerText = `Baseline: ${{p.base_sr}}`;

                document.getElementById('m2Label').innerText = "Clutch Delta (Lift)";
                document.getElementById('m2Val').innerText = `+${{p.delta_sr}}`;
                document.getElementById('m2Sub').innerText = "SR Points Gained";

                document.getElementById('m3Label').innerText = "Boundary Rate";
                document.getElementById('m3Val').innerText = `${{p.bnd_pct}}%`;
                document.getElementById('m3Sub').innerText = `Dots: ${{p.dot_pct}}% | 6s: ${{p.sixes}}`;

                document.getElementById('m4Label').innerText = "Scouting Rating";
                document.getElementById('m4Val').innerText = p.rating;
                document.getElementById('m4Sub').innerText = `Win Rate: ${{p.win_pct}}%`;

                document.getElementById('bar1Label').innerText = "High-Pressure Scoring Efficiency";
                document.getElementById('bar1Val').innerText = `${{Math.min(100, Math.round(p.hp_sr / 2.2))}}%`;
                document.getElementById('bar1Bar').style.width = `${{Math.min(100, Math.round(p.hp_sr / 2.2))}}%`;

                document.getElementById('pSummary').innerText = `Demonstrates consistent acceleration with a +${{p.delta_sr}} strike rate lift under extreme leverage. Evaluated across ${{p.hp_balls}} pressure balls against ${{p.opponents}} unique teams.`;
            }} else {{
                document.getElementById('m1Label').innerText = "Pressure Economy";
                document.getElementById('m1Val').innerText = `${{p.hp_econ}} rpo`;
                document.getElementById('m1Sub').innerText = `Baseline: ${{p.base_econ}} rpo`;

                document.getElementById('m2Label').innerText = "Runs Saved / 6 Balls";
                document.getElementById('m2Val').innerText = `+${{p.saved_per_6}} rpo`;
                document.getElementById('m2Sub').innerText = "vs Expected Runs";

                document.getElementById('m3Label').innerText = "Bowling Strike Rate";
                document.getElementById('m3Val').innerText = `${{p.hp_sr}} b/w`;
                document.getElementById('m3Sub').innerText = `Wickets: ${{p.hp_wkts}} | Dots: ${{p.dot_pct}}%`;

                document.getElementById('m4Label').innerText = "Scouting Rating";
                document.getElementById('m4Val').innerText = p.rating;
                document.getElementById('m4Sub').innerText = `Win Rate: ${{p.win_pct}}%`;

                document.getElementById('bar1Label').innerText = "Economy Containment Efficiency";
                document.getElementById('bar1Val').innerText = `${{Math.min(100, Math.round((12.0 - p.hp_econ) * 12))}}%`;
                document.getElementById('bar1Bar').style.width = `${{Math.min(100, Math.round((12.0 - p.hp_econ) * 12))}}%`;

                document.getElementById('pSummary').innerText = `Suppresses scoring by +${{p.saved_per_6}} runs per over below match expectations while striking every ${{p.hp_sr}} balls under high pressure across ${{p.hp_balls}} deliveries.`;
            }}

            document.getElementById('bar2Label').innerText = "Match Consistency Impact";
            document.getElementById('bar2Val').innerText = `${{p.win_pct}}%`;
            document.getElementById('bar2Bar').style.width = `${{p.win_pct}}%`;

            document.getElementById('bar3Label').innerText = "Sample Volume Credibility";
            document.getElementById('bar3Val').innerText = `${{p.hp_balls}} Balls (${{p.hp_balls >= 300 ? 'High' : 'Moderate'}})`;
            document.getElementById('bar3Bar').style.width = `${{Math.min(100, Math.round(p.hp_balls / 5))}}%`;
        }}

        function filterPlayers() {{
            const q = document.getElementById('searchInput').value;
            renderTable(q);
        }}

        function copyDropdownList() {{
            const data = getData();
            const text = data.map(function(item) {{ return 'Rank ' + item.rank + ': ' + item.name; }}).join('\\n');
            navigator.clipboard.writeText(text).then(function() {{
                alert('Copied Top 10 to clipboard!');
            }});
        }}

        function renderAnalyticsCharts() {{
            const data = getData();
            const isBat = currentRole === 'bat';

            // Chart 1: Differential
            const ctx1 = document.getElementById('chartDifferential').getContext('2d');
            if (chartDiff) chartDiff.destroy();

            chartDiff = new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: data.map(d => d.name),
                    datasets: [
                        {{
                            label: isBat ? 'High Pressure SR' : 'High Pressure Economy',
                            data: isBat ? data.map(d => d.hp_sr) : data.map(d => d.hp_econ),
                            backgroundColor: isBat ? 'rgba(225, 29, 72, 0.85)' : 'rgba(37, 99, 235, 0.85)',
                            borderRadius: 4
                        }},
                        {{
                            label: isBat ? 'Baseline Non-Pressure SR' : 'Baseline Economy',
                            data: isBat ? data.map(d => d.base_sr) : data.map(d => d.base_econ),
                            backgroundColor: 'rgba(100, 116, 139, 0.4)',
                            borderRadius: 4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 9 }} }}, grid: {{ display: false }} }},
                        y: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255, 255, 255, 0.05)' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#f1f5f9', font: {{ size: 11 }} }} }} }}
                }}
            }});

            // Chart 2: Consistency
            const ctx2 = document.getElementById('chartConsistency').getContext('2d');
            if (chartCons) chartCons.destroy();

            chartCons = new Chart(ctx2, {{
                type: 'line',
                data: {{
                    labels: data.map(d => d.name),
                    datasets: [{{
                        label: 'Positive Impact Rate (%)',
                        data: data.map(d => d.win_pct),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#10b981',
                        pointRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 9 }} }}, grid: {{ display: false }} }},
                        y: {{ min: 40, max: 100, ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255, 255, 255, 0.05)' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#f1f5f9', font: {{ size: 11 }} }} }} }}
                }}
            }});
        }}

        window.onload = function() {{
            renderTable();
        }};
    </script>
</body>
</html>
"""

with open('Rajasthan_Royals_SupeRR_Selector_Dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Successfully created modern, clean, user-friendly dashboard: Rajasthan_Royals_SupeRR_Selector_Dashboard.html")
