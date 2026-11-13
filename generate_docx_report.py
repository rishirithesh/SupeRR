import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import pandas as pd

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_docx_report(filename="Rajasthan_Royals_SupeRR_Selector_Methodology_Report.docx"):
    doc = docx.Document()

    # Set margins
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    # Styles
    p_meta = doc.add_paragraph()
    run_meta = p_meta.add_run("RAJASTHAN ROYALS | SupeRR SELECTOR SEASON 2")
    run_meta.font.name = "Arial"
    run_meta.font.size = Pt(10)
    run_meta.font.bold = True
    run_meta.font.color.rgb = RGBColor(224, 58, 62) # Royals Pink

    p_title = doc.add_paragraph()
    run_title = p_title.add_run("Clutch Under Fire: A Principled Data-Driven Framework for Identifying and Ranking High-Pressure Cricket Talent")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(29, 66, 138) # Royal Blue

    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run("Official Round 1 Technical & Methodology Report | Prepared for Rajasthan Royals Cricket Operations & Scouting Management")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 100, 100)

    # Executive Summary Box
    t_box = doc.add_table(rows=1, cols=1)
    t_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t_box.cell(0, 0)
    set_cell_background(cell, "EFF6FF")
    p_box = cell.paragraphs[0]
    r_box = p_box.add_run(
        "Executive Summary: Identifying cricketers who reliably outperform under severe pressure is the holy grail of T20 franchise operations. "
        "Traditional metrics (raw batting strike rate, bowling economy) obscure clutch capability because they conflate low-stakes stat-padding with genuine high-stakes execution. "
        "In this report, we construct a mathematically rigorous, delivery-level Rajasthan Royals Pressure Index (RR-PI ∈ [0, 100]) that evaluates match urgency, required run rates, wicket depletion, win-probability leverage, and tournament stakes across 200,999 deliveries (IPL and T20Is, 2022–2026). "
        "By comparing high-pressure performance against player-specific baselines and competition-context expectations using Empirical Bayes shrinkage, we isolate true clutch differentials. "
        "The resulting Top 10 Batters and Top 10 Bowlers represent evidence-backed, high-conviction targets for the Rajasthan Royals franchise."
    )
    r_box.font.name = "Arial"
    r_box.font.size = Pt(9.5)
    r_box.font.color.rgb = RGBColor(30, 58, 138)

    doc.add_paragraph()

    # Section 1
    h1 = doc.add_heading("1. Pressure Definition: Match Situations & Indicators", level=1)
    h1.runs[0].font.color.rgb = RGBColor(29, 66, 138)
    
    p = doc.add_paragraph(
        "Pressure in T20 cricket is multifaceted and fundamentally asymmetric across innings. Rather than utilizing ad-hoc filters (e.g. arbitrarily selecting overs 18–20), we model pressure as a continuous, dynamic state variable for every single delivery:"
    )
    p.runs[0].font.size = Pt(10)

    bullets = [
        ("Innings 2 (Chasing Pressure): ", "Driven by three interacting forces: (1) Win Probability Leverage (L = 4 · WP · (1-WP)), which peaks when the game is 50-50 and approaches zero in blowouts; (2) Rate & Resource Stress, scaling as Required Run Rate (RRR) exceeds the baseline (8.2 rpo) magnified by remaining wicket scarcity (W_rem ≤ 4); and (3) Late-Innings Closeness, surging in the final 24 deliveries when the margin is within 45 runs."),
        ("Innings 1 (Target Setting Pressure): ", "Modeled through: (1) Phase Baselines, recognizing that death overs (16–20) have high expected variance; (2) Early Wicket Crisis, where top-order collapses (≥2 wickets in Powerplay, ≥4 before over 12) force batters to rebuild without forfeiting scoring momentum; and (3) Par Deficit Stress, penalizing falling behind expected venue par."),
        ("Tournament Criticality: ", "Knockout and playoff matches (knock_out == 1) receive a 1.15× multiplier to account for career-defining stakes."),
        ("High-Pressure Operational Cutoff: ", "We calibrate the index so that the upper quartile (75th percentile, PI ≥ 65.0) constitutes High-Pressure Situations. Across the entire 200,999 ball dataset, exactly 50,255 deliveries (25.0%) qualify, with 27.9% in Innings 1 and 21.8% in Innings 2, ensuring fair representation.")
    ]
    for b_title, b_text in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = bp.add_run(b_text)
        r2.font.size = Pt(9.5)

    if os.path.exists("visualizations/pressure_index_distribution.png"):
        doc.add_paragraph()
        doc.add_picture("visualizations/pressure_index_distribution.png", width=Inches(6.2))
        cp = doc.add_paragraph("Figure 1: Distribution of Rajasthan Royals Delivery-Level Pressure Index (RR-PI), highlighting the PI ≥ 65 cutoff.")
        cp.runs[0].font.size = Pt(8.5)
        cp.runs[0].font.italic = True
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Section 2
    h2 = doc.add_heading("2. Performance Measurement & Rating Logic", level=1)
    h2.runs[0].font.color.rgb = RGBColor(29, 66, 138)
    
    p2 = doc.add_paragraph(
        "To satisfy the mandate of measuring performance compared with usual levels, our scoring system incorporates both Absolute Pressure Impact and Clutch Differentials (Δ) relative to player baselines:"
    )
    p2.runs[0].font.size = Pt(10)

    b_s2 = [
        ("Batting Metric Suite: ", "High-Pressure Strike Rate (SR_HP), Batting Average (Avg_HP), Boundary Execution % (4s & 6s), Dot Ball Minimization %, and Context-Adjusted Runs Above Expected (RAE100). The Clutch Strike Rate Delta (ΔSR = SR_HP - SR_Base) measures whether a batter accelerates under fire or slows down."),
        ("Bowling Metric Suite: ", "High-Pressure Economy (Econ_HP), Bowling Strike Rate (Balls/Wkt), Runs Saved Above Expected per over (RSAE6), Dot Ball % creation, and Boundary Conceded suppression. The Clutch Economy Delta (ΔEcon = Econ_Base - Econ_HP) measures run suppression gains under pressure."),
        ("Empirical Bayes Shrinkage (K = 60 balls): ", "Raw rates over small samples are notoriously unstable. We shrink each player's high-pressure rate toward the empirical population mean (SR_reg = (N·SR + 60·SR_pop)/(N + 60)), ensuring small-sample anomalies cannot artificially top the rankings."),
        ("Sample Credibility Weighting: ", "A volume confidence factor (√(N_HP) / √(300)) rewards sustained execution across multiple seasons over flash-in-the-pan bursts.")
    ]
    for b_title, b_text in b_s2:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = bp.add_run(b_text)
        r2.font.size = Pt(9.5)

    # Section 3
    h3 = doc.add_heading("3. Fair Comparisons: Context Normalization (IPL vs T20I)", level=1)
    h3.runs[0].font.color.rgb = RGBColor(29, 66, 138)
    
    p3 = doc.add_paragraph(
        "Our empirical analysis revealed profound environmental differences across competition formats. Under high pressure (PI ≥ 65), the baseline IPL scoring rate is 9.70 rpo (161.71 SR), compared to 8.79 rpo (146.46 SR) in T20Is — a massive 15.25 SR point disparity! Failing to account for this would severely penalize IPL death bowlers and artificially flatter batters facing second-tier international attacks."
    )
    p3.runs[0].font.size = Pt(10)

    b_s3 = [
        ("Competition Tier Weighting: ", "Tier 1 (IPL, Asia Cup: 1.00×), Tier 2 (Top 8 Full Member bilaterals: 0.92×), Tier 3 (Associate / Emerging / Rising Stars tournaments: 0.75×)."),
        ("Eligibility Thresholds: ", "To be considered for Top 10 franchise selection, batters must have faced ≥ 80 legal HP balls (≥ 200 total), and bowlers must have delivered ≥ 90 legal HP balls (≥ 240 total).")
    ]
    for b_title, b_text in b_s3:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = bp.add_run(b_text)
        r2.font.size = Pt(9.5)

    # Section 4
    h4 = doc.add_heading("4. Evidence & Detailed Rankings for Rajasthan Royals", level=1)
    h4.runs[0].font.color.rgb = RGBColor(29, 66, 138)

    # Batters Table
    h4_b = doc.add_heading("Official Top 10 Batters Under Pressure (Dropdown Selections: Rank 1 to 10)", level=2)
    h4_b.runs[0].font.color.rgb = RGBColor(224, 58, 62)

    top_b = pd.read_csv('top_10_batters_under_pressure.csv')
    t_bat = doc.add_table(rows=len(top_b)+1, cols=11)
    t_bat.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers_b = ["Rank", "Batter Name", "HP Balls", "HP Runs", "HP SR", "Base SR", "Δ SR", "HP Avg", "Bnd %", "Win %", "Rating"]
    for col_idx, h in enumerate(headers_b):
        cell = t_bat.cell(0, col_idx)
        set_cell_background(cell, "1D428A")
        cp = cell.paragraphs[0]
        cr = cp.add_run(h)
        cr.font.name = "Arial"
        cr.font.size = Pt(8)
        cr.font.bold = True
        cr.font.color.rgb = RGBColor(255, 255, 255)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for row_idx, r in top_b.iterrows():
        vals = [
            str(int(r['rank'])),
            str(r['striker_name']),
            str(int(r['hp_balls'])),
            str(int(r['hp_runs'])),
            f"{r['hp_sr']:.1f}",
            f"{r['lp_sr']:.1f}",
            f"+{r['clutch_sr_delta']:.1f}",
            f"{r['hp_avg']:.1f}",
            f"{r['hp_boundary_pct']:.1f}%",
            f"{r['positive_impact_pct']:.1f}%",
            f"{r['rating']:.2f}"
        ]
        bg = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(vals):
            cell = t_bat.cell(row_idx+1, col_idx)
            set_cell_background(cell, bg)
            cp = cell.paragraphs[0]
            cr = cp.add_run(val)
            cr.font.name = "Arial"
            cr.font.size = Pt(8)
            if col_idx in [0, 1, 6, 10]:
                cr.font.bold = True
            cp.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 1 else WD_ALIGN_PARAGRAPH.CENTER

    if os.path.exists("visualizations/top_10_batters_strike_rates.png"):
        doc.add_paragraph()
        doc.add_picture("visualizations/top_10_batters_strike_rates.png", width=Inches(6.2))
        cp = doc.add_paragraph("Figure 2: Top 10 Batters High-Pressure Strike Rate vs Baseline Platform, emphasizing positive clutch elevation.")
        cp.runs[0].font.size = Pt(8.5)
        cp.runs[0].font.italic = True
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Bowlers Table
    h4_bw = doc.add_heading("Official Top 10 Bowlers Under Pressure (Dropdown Selections: Rank 1 to 10)", level=2)
    h4_bw.runs[0].font.color.rgb = RGBColor(224, 58, 62)

    top_bw = pd.read_csv('top_10_bowlers_under_pressure.csv')
    t_bowl = doc.add_table(rows=len(top_bw)+1, cols=11)
    t_bowl.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers_bw = ["Rank", "Bowler Name", "HP Balls", "HP Wkts", "HP Econ", "Base Econ", "Saved/6", "HP SR", "Dot %", "Win %", "Rating"]
    for col_idx, h in enumerate(headers_bw):
        cell = t_bowl.cell(0, col_idx)
        set_cell_background(cell, "1D428A")
        cp = cell.paragraphs[0]
        cr = cp.add_run(h)
        cr.font.name = "Arial"
        cr.font.size = Pt(8)
        cr.font.bold = True
        cr.font.color.rgb = RGBColor(255, 255, 255)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for row_idx, r in top_bw.iterrows():
        vals = [
            str(int(r['rank'])),
            str(r['bowler_name']),
            str(int(r['hp_balls'])),
            str(int(r['hp_wickets'])),
            f"{r['hp_econ']:.2f}",
            f"{r['lp_econ']:.2f}",
            f"+{r['hp_rsae6_w']:.2f}",
            f"{r['hp_sr']:.1f}",
            f"{r['hp_dot_pct']:.1f}%",
            f"{r['positive_impact_pct']:.1f}%",
            f"{r['rating']:.2f}"
        ]
        bg = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(vals):
            cell = t_bowl.cell(row_idx+1, col_idx)
            set_cell_background(cell, bg)
            cp = cell.paragraphs[0]
            cr = cp.add_run(val)
            cr.font.name = "Arial"
            cr.font.size = Pt(8)
            if col_idx in [0, 1, 4, 6, 10]:
                cr.font.bold = True
            cp.alignment = WD_ALIGN_PARAGRAPH.LEFT if col_idx == 1 else WD_ALIGN_PARAGRAPH.CENTER

    if os.path.exists("visualizations/top_10_bowlers_economy.png"):
        doc.add_paragraph()
        doc.add_picture("visualizations/top_10_bowlers_economy.png", width=Inches(6.2))
        cp = doc.add_paragraph("Figure 3: Top 10 Bowlers High-Pressure Economy vs Baseline, highlighting net runs saved per over.")
        cp.runs[0].font.size = Pt(8.5)
        cp.runs[0].font.italic = True
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Section 5: Player Dossiers
    h5 = doc.add_heading("5. Detailed Tactical Dossiers for Top Selections", level=1)
    h5.runs[0].font.color.rgb = RGBColor(29, 66, 138)

    dossiers_b = [
        ("Rank 1 Batter — Babar Azam (Rating: 89.37): ", "Contrary to public perception of anchor play, Babar's numbers in genuine high-pressure match situations (PI ≥ 65) are transcendent. He records an astonishing 219.57 HP strike rate (compared to 126.03 baseline, a clutch delta of +93.53 SR!), averaging 67.33 with an ultra-low 13.04% dot ball rate across 92 pressure balls. He delivered a positive net impact in 88.9% of pressure matches."),
        ("Rank 2 Batter — Suryakumar Yadav (Rating: 84.75): ", "The gold standard of sustained volume and lethality. Over 426 high-pressure balls in IPL and international cricket, SKY strikes at 215.49 (+57.84 delta over 157.65 baseline). Over 34.2% of his high-pressure deliveries result in boundaries (one boundary every 2.9 balls). In 74.4% of games, his high-pressure batting produced a game-winning run contribution."),
        ("Rank 3 Batter — Najibullah Zadran (Rating: 75.38): ", "Afghanistan's premier crisis manager elevates from a modest 109.18 baseline SR to 197.94 under pressure (+88.76 SR delta), averaging 48.00 with 81.8% match consistency."),
        ("Rank 4 Batter — Tristan Stubbs (Rating: 73.24): ", "A prototype modern 360-degree death specialist. Across 489 pressure deliveries, Stubbs boasts an elite 183.03 HP SR (+61.03 delta) and 38.91 average, maintaining a tiny 22.09% dot rate against elite death bowling."),
        ("Rank 5 Batter — Rishabh Pant (Rating: 73.06): ", "Rebounds with remarkable clutch conviction. Strikes at exactly 200.00 under pressure (+73.03 delta over 126.97 baseline), with 31.02% boundary hitting and 72.0% positive match rate."),
        ("Rank 6 Batter — Namboori Tilak Varma (Rating: 72.57): ", "Faced the largest high-pressure sample in the entire dataset (634 balls, 1178 runs). Demonstrates uncanny temperament, striking at 185.80 (+57.67 delta) with a 36.81 average and 64.4% positive impact rate."),
        ("Rank 7 Batter — Naman Dhir (Rating: 69.53): ", "The emerging breakout talent of 2024–2026. Across 199 pressure balls, strikes at 205.03 (+54.90 delta) with 31.16% boundaries, providing immense auction utility."),
        ("Rank 8 Batter — Matthew Wade (Rating: 69.43): ", "Veteran finishing masterclass. Strikes at 165.45 under pressure (+50.06 delta) while averaging an incredible 63.20 per dismissal."),
        ("Rank 9 Batter — Rovman Powell (Rating: 68.53): ", "Rajasthan Royals' trusted enforcer. Over 572 high-pressure balls, Powell scored 1061 runs at 185.49 SR (+60.77 delta), clearing ropes on 26.4% of balls."),
        ("Rank 10 Batter — Glenn Phillips (Rating: 68.42): ", "Dynamic multi-dimensional finisher with 204.59 HP SR (+70.15 delta) and 27.06% boundaries.")
    ]
    for p_name, text in dossiers_b:
        p = doc.add_paragraph()
        r1 = p.add_run(p_name)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = p.add_run(text)
        r2.font.size = Pt(9.5)

    doc.add_paragraph()

    dossiers_bw = [
        ("Rank 1 Bowler — Sunil Narine (Rating: 97.05): ", "The ultimate pressure strangler. Across 310 high-pressure balls in the IPL, Narine boasts an unbelievable 5.92 Economy Rate (saving +3.78 runs per over vs expectation), taking 24 wickets at a 12.92 strike rate with 44.19% dots. His economy actually improves under pressure (6.97 baseline vs 5.92 HP). In 90.7% of pressure matches, Narine delivered a positive net run-suppression value."),
        ("Rank 2 Bowler — Mohammad Nawaz (Rating: 95.86): ", "Phenomenal left-arm control in tight chokes. Across 124 HP balls, concedes just 4.59 rpo (+3.73 runs saved/over) with a blistering 8.86 bowling strike rate, 50.81% dot rate, and 93.3% match positive rate."),
        ("Rank 3 Bowler — Abrar Ahmed (Rating: 90.89): ", "Mystery leg-spin execution. Across 204 HP balls, concedes 5.06 rpo with an 11.33 strike rate and 48.04% dots (88.0% consistency)."),
        ("Rank 4 Bowler — Sufiyan Muqeem (Rating: 90.45): ", "Left-arm wrist spin prodigy. 4.84 HP economy and 61.24% dot balls across 129 HP deliveries (92.9% consistency)."),
        ("Rank 5 Bowler — Umran Malik (Rating: 86.59): ", "Pure strike enforcer. Under high pressure, Umran's economy drops dramatically from 9.73 down to 7.03 rpo (+2.70 improvement!), while striking every 7.88 balls (17 wickets in 134 HP balls) with 52.24% dot balls."),
        ("Rank 6 Bowler — Matheesha Pathirana (Rating: 80.04): ", "The premier death-overs pace weapon. Delivered an extraordinary 560 high-pressure balls (taking 50 wickets!) with a 7.71 economy in an IPL environment where death expectation is 9.70, striking at 11.20 balls per wicket with 80.5% match consistency."),
        ("Rank 7 Bowler — Mitchell Santner (Rating: 75.48): ", "Elite accuracy. 6.77 HP economy across 288 balls, saving 2.07 runs/over with 13.71 strike rate."),
        ("Rank 8 Bowler — Shadab Khan (Rating: 75.41): ", "Middle/death overs leg-spin weapon. Concedes 6.54 HP rpo (12.00 strike rate, 41.67% dots)."),
        ("Rank 9 Bowler — Spencer Johnson (Rating: 73.95): ", "Left-arm high-pace execution. 7.50 HP economy (+1.67 runs saved/over, 10.67 SR, 92.3% positive match rate)."),
        ("Rank 10 Bowler — Kuldeep Yadav (Rating: 73.70): ", "India's premier wrist-spinner. 438 HP balls, 34 wickets, 7.90 HP economy, 12.88 strike rate, 38.13% dots.")
    ]
    for p_name, text in dossiers_bw:
        p = doc.add_paragraph()
        r1 = p.add_run(p_name)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = p.add_run(text)
        r2.font.size = Pt(9.5)

    # Section 6
    h6 = doc.add_heading("6. Reliability, Consistency Checks & Model Limitations", level=1)
    h6.runs[0].font.color.rgb = RGBColor(29, 66, 138)

    b_s6 = [
        ("Match Consistency Verification: ", "Every player in our Top 10 boasts a Positive Match Contribution Rate exceeding 50% (and averaging 70–93%), confirming that their ratings reflect repeatable, game-in game-out reliability rather than one outlier performance."),
        ("Opposition Breadth: ", "All top 10 bowlers and batters faced at least 8 to 16 distinct opposition franchises/nations under pressure, proving cross-opponent robustness."),
        ("Innings Distribution: ", "Top batters showed strong balance across target chasing (Innings 2) and target setting / crisis management (Innings 1). For example, Tilak Varma recorded 382 balls in Innings 1 and 252 balls in Innings 2; Suryakumar Yadav faced 248 balls in Innings 1 and 178 balls in Innings 2."),
        ("Known Model Limitations: ", "(1) Tracking Absence: The supplied dataset lacks Hawk-Eye ball tracking (pitch coordinates, release height, deviation), so bowling ratings measure outcome execution rather than pitch execution; (2) Fielding Noise: Dropped catches and misfields inevitably inject slight variance into bowler runs and batter dismissals; and (3) Sample Asymmetry: High-volume IPL veterans (Pathirana, Narine, SKY, Tilak) carry tighter posterior credible intervals than emerging talents (Spencer Johnson, Naman Dhir), although our Bayesian shrinkage explicitly penalizes small-sample variance.")
    ]
    for b_title, b_text in b_s6:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = bp.add_run(b_text)
        r2.font.size = Pt(9.5)

    # Section 7
    h7 = doc.add_heading("7. Franchise Strategy & Auction Recommendations for Rajasthan Royals", level=1)
    h7.runs[0].font.color.rgb = RGBColor(29, 66, 138)

    b_s7 = [
        ("Death Bowling Asset Priority: ", "Matheesha Pathirana (50 wickets, 7.71 Econ in death-heavy pressure) and Spencer Johnson (left-arm pace, 7.50 Econ) represent tier-1 pace targets to complement existing attack structures."),
        ("Middle-Overs Pressure Choke: ", "Sunil Narine (5.92 Econ under pressure) and Mitchell Santner (6.77 Econ) prove that elite spin is the most reliable mechanism to suppress high-pressure chases."),
        ("Finishers with High Clutch Deltas: ", "Players like Tristan Stubbs (+61.0 ΔSR), Rovman Powell (+60.8 ΔSR), and Naman Dhir (+54.9 ΔSR) demonstrate the psychological resilience to accelerate when match pressure peaks."),
        ("Retention Validation: ", "Rovman Powell's top-10 ranking (Rating 68.53, 572 pressure balls) strongly vindicates his strategic value to the Royals' finishing core.")
    ]
    for b_title, b_text in b_s7:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(b_title)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r2 = bp.add_run(b_text)
        r2.font.size = Pt(9.5)

    doc.add_paragraph()
    p_sign = doc.add_paragraph()
    r_sign = p_sign.add_run("Submission Assurance: All 20 player names in this report match verbatim with competition_team_player_mapping.csv and are directly selectable via the Unstop dropdown fields. Prepared by the Senior Sports Data Scientist & Auction Strategy Consultant for Rajasthan Royals.")
    r_sign.font.size = Pt(8.5)
    r_sign.font.italic = True
    r_sign.font.color.rgb = RGBColor(100, 100, 100)

    doc.save(filename)
    print(f"Word document report created successfully: {filename}")

if __name__ == '__main__':
    create_docx_report()
