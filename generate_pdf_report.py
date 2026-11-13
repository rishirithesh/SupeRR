import os
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Rajasthan Royals | SupeRR Selector Season 2 — Round 1 Technical Report")
            self.drawRightString(558, 755, "Confidential Analytics")
            self.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.drawString(54, 32, "Rajasthan Royals Decision Science & Cricket Analytics Group")
        self.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.setLineWidth(0.5)
        self.line(54, 44, 558, 44)
        self.restoreState()

def build_pdf_report(filename="Rajasthan_Royals_SupeRR_Selector_Methodology_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#1D428A")     # Royal Blue
    accent_color = colors.HexColor("#E03A3E")      # Royals Pink / Crimson
    dark_neutral = colors.HexColor("#1F2937")
    light_bg = colors.HexColor("#F9FAFB")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=accent_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=dark_neutral,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=dark_neutral,
        leftIndent=12,
        spaceAfter=2.5
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1E3A8A")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        leading=8.5,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9,
        textColor=dark_neutral,
        alignment=1
    )

    table_cell_left = ParagraphStyle(
        'TableCellLeft',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9,
        textColor=dark_neutral,
        alignment=0
    )

    story = []

    # PAGE 1: Title, Executive Summary, Section 1 & Distribution Chart
    story.append(Paragraph("RAJASTHAN ROYALS | SupeRR SELECTOR SEASON 2", ParagraphStyle('SuperTitle', fontName='Helvetica-Bold', fontSize=8.5, textColor=accent_color, spaceAfter=3)))
    story.append(Paragraph("Clutch Under Fire: A Principled Data-Driven Framework for Identifying and Ranking High-Pressure Cricket Talent", title_style))
    story.append(Paragraph("<b>Official Round 1 Technical & Methodology Report</b> | Prepared for Rajasthan Royals Cricket Operations & Scouting Management", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8))

    summary_text = (
        "<b>Executive Summary:</b> Identifying cricketers who reliably outperform under severe pressure is the holy grail of T20 franchise operations. "
        "Traditional metrics (raw batting strike rate, bowling economy) obscure clutch capability because they conflate low-stakes stat-padding with genuine high-stakes execution. "
        "In this report, we construct a mathematically rigorous, delivery-level <b>Rajasthan Royals Pressure Index (RR-PI ∈ [0, 100])</b> that evaluates match urgency, required run rates, wicket depletion, win-probability leverage, and tournament stakes across 200,999 deliveries (IPL and T20Is, 2022–2026). "
        "By comparing high-pressure performance against player-specific baselines and competition-context expectations using Empirical Bayes shrinkage, we isolate true clutch differentials. "
        "The resulting Top 10 Batters and Top 10 Bowlers represent evidence-backed, high-conviction targets for the Rajasthan Royals franchise."
    )
    summary_table = Table([[Paragraph(summary_text, callout_style)]], colWidths=[504])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BFDBFE")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Pressure Definition: Match Situations & Indicators", h1_style))
    story.append(Paragraph(
        "Pressure in T20 cricket is multifaceted and fundamentally asymmetric across innings. Rather than utilizing ad-hoc filters (e.g. arbitrarily selecting overs 18–20), we model pressure as a continuous, dynamic state variable for every single delivery:",
        body_style
    ))
    story.append(Paragraph("• <b>Innings 2 (Chasing Pressure):</b> Driven by three interacting forces: (1) <i>Win Probability Leverage</i> (L = 4 · WP · (1-WP)), which peaks when the game is 50-50 and approaches zero in blowouts; (2) <i>Rate & Resource Stress</i>, scaling as Required Run Rate (RRR) exceeds the baseline (8.2 rpo) magnified by remaining wicket scarcity (W_rem ≤ 4); and (3) <i>Late-Innings Closeness</i>, surging in the final 24 deliveries when the margin is within 45 runs.", bullet_style))
    story.append(Paragraph("• <b>Innings 1 (Target Setting Pressure):</b> Modeled through: (1) <i>Phase Baselines</i>, recognizing that death overs (16–20) have high expected variance; (2) <i>Early Wicket Crisis</i>, where top-order collapses (≥2 wickets in Powerplay, ≥4 before over 12) force batters to rebuild without forfeiting scoring momentum; and (3) <i>Par Deficit Stress</i>, penalizing falling behind expected venue par.", bullet_style))
    story.append(Paragraph("• <b>Tournament Criticality:</b> Knockout and playoff matches (knock_out == 1) receive a 1.15× multiplier to account for career-defining stakes.", bullet_style))
    story.append(Paragraph("• <b>High-Pressure Operational Cutoff:</b> We calibrate the index so that the upper quartile (75th percentile, <b>PI ≥ 65.0</b>) constitutes <i>High-Pressure Situations</i>. Across the entire 200,999 ball dataset, exactly 50,255 deliveries (25.0%) qualify, with 27.9% in Innings 1 and 21.8% in Innings 2, ensuring fair representation.", bullet_style))
    
    if os.path.exists('visualizations/pressure_index_distribution.png'):
        story.append(Spacer(1, 4))
        story.append(Image('visualizations/pressure_index_distribution.png', width=6.8*inch, height=2.2*inch))
        story.append(Paragraph("<i>Figure 1: Distribution of Rajasthan Royals Delivery-Level Pressure Index (RR-PI), highlighting the PI ≥ 65 cutoff.</i>", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor("#6B7280"), alignment=1)))

    story.append(PageBreak())

    # PAGE 2: Section 2 & Section 3
    story.append(Paragraph("2. Performance Measurement & Rating Logic", h1_style))
    story.append(Paragraph(
        "To satisfy the mandate of measuring performance <i>compared with usual levels</i>, our scoring system incorporates both <b>Absolute Pressure Impact</b> and <b>Clutch Differentials (Δ)</b> relative to player baselines:",
        body_style
    ))
    story.append(Paragraph("• <b>Batting Metric Suite:</b> High-Pressure Strike Rate (SR_HP), Batting Average (Avg_HP), Boundary Execution % (4s & 6s), Dot Ball Minimization %, and Context-Adjusted Runs Above Expected (RAE100). The <i>Clutch Strike Rate Delta</i> (ΔSR = SR_HP - SR_Base) measures whether a batter accelerates under fire or slows down.", bullet_style))
    story.append(Paragraph("• <b>Bowling Metric Suite:</b> High-Pressure Economy (Econ_HP), Bowling Strike Rate (Balls/Wkt), Runs Saved Above Expected per over (RSAE6), Dot Ball % creation, and Boundary Conceded suppression. The <i>Clutch Economy Delta</i> (ΔEcon = Econ_Base - Econ_HP) measures run suppression gains under pressure.", bullet_style))
    story.append(Paragraph("• <b>Empirical Bayes Shrinkage (K = 60 balls):</b> Raw rates over small samples are notoriously unstable. We shrink each player's high-pressure rate toward the empirical population mean (SR_reg = (N·SR + 60·SR_pop)/(N + 60)), ensuring small-sample anomalies cannot artificially top the rankings.", bullet_style))
    story.append(Paragraph("• <b>Sample Credibility Weighting:</b> A volume confidence factor (√(N_HP) / √(300)) rewards sustained execution across multiple seasons over flash-in-the-pan bursts.", bullet_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Fair Comparisons: Context Normalization (IPL vs T20I)", h1_style))
    story.append(Paragraph(
        "Our empirical analysis revealed profound environmental differences across competition formats. Under high pressure (PI ≥ 65), the baseline IPL scoring rate is <b>9.70 rpo (161.71 SR)</b>, compared to <b>8.79 rpo (146.46 SR)</b> in T20Is — a massive 15.25 SR point disparity! Failing to account for this would severely penalize IPL death bowlers and artificially flatter batters facing second-tier international attacks.",
        body_style
    ))
    story.append(Paragraph("• <b>Competition Tier Weighting:</b> Tier 1 (IPL, Asia Cup: 1.00×), Tier 2 (Top 8 Full Member bilaterals: 0.92×), Tier 3 (Associate / Emerging / Rising Stars tournaments: 0.75×).", bullet_style))
    story.append(Paragraph("• <b>Eligibility Thresholds:</b> To be considered for Top 10 franchise selection, batters must have faced ≥ 80 legal HP balls (≥ 200 total), and bowlers must have delivered ≥ 90 legal HP balls (≥ 240 total).", bullet_style))
    story.append(Spacer(1, 8))

    # Evidence & Batters Table
    story.append(Paragraph("4. Evidence & Detailed Rankings for Rajasthan Royals", h1_style))
    story.append(Paragraph("Official Top 10 Batters Under Pressure (Dropdown Selections: Rank 1 to 10)", h2_style))
    top_b = pd.read_csv('top_10_batters_under_pressure.csv')
    
    b_table_data = [
        [
            Paragraph("<b>Rank</b>", table_header_style),
            Paragraph("<b>Batter Name</b>", table_header_style),
            Paragraph("<b>HP Balls</b>", table_header_style),
            Paragraph("<b>HP Runs</b>", table_header_style),
            Paragraph("<b>HP SR</b>", table_header_style),
            Paragraph("<b>Base SR</b>", table_header_style),
            Paragraph("<b>Δ SR</b>", table_header_style),
            Paragraph("<b>HP Avg</b>", table_header_style),
            Paragraph("<b>Bnd %</b>", table_header_style),
            Paragraph("<b>Dot %</b>", table_header_style),
            Paragraph("<b>Win %</b>", table_header_style),
            Paragraph("<b>Rating</b>", table_header_style)
        ]
    ]
    for _, r in top_b.iterrows():
        b_table_data.append([
            Paragraph(f"<b>{int(r['rank'])}</b>", table_cell_style),
            Paragraph(f"<b>{r['striker_name']}</b>", table_cell_left),
            Paragraph(f"{int(r['hp_balls'])}", table_cell_style),
            Paragraph(f"{int(r['hp_runs'])}", table_cell_style),
            Paragraph(f"{r['hp_sr']:.1f}", table_cell_style),
            Paragraph(f"{r['lp_sr']:.1f}", table_cell_style),
            Paragraph(f"<b>+{r['clutch_sr_delta']:.1f}</b>", table_cell_style),
            Paragraph(f"{r['hp_avg']:.1f}", table_cell_style),
            Paragraph(f"{r['hp_boundary_pct']:.1f}%", table_cell_style),
            Paragraph(f"{r['hp_dot_pct']:.1f}%", table_cell_style),
            Paragraph(f"{r['positive_impact_pct']:.1f}%", table_cell_style),
            Paragraph(f"<b>{r['rating']:.2f}</b>", table_cell_style),
        ])

    t_bat = Table(b_table_data, colWidths=[24, 95, 36, 36, 40, 38, 38, 36, 38, 36, 38, 49])
    t_bat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_bat)

    story.append(PageBreak())

    # PAGE 3: Batters Chart & Bowlers Table & Chart
    if os.path.exists('visualizations/top_10_batters_strike_rates.png'):
        story.append(Image('visualizations/top_10_batters_strike_rates.png', width=6.8*inch, height=2.4*inch))
        story.append(Paragraph("<i>Figure 2: Top 10 Batters High-Pressure Strike Rate vs Baseline Platform, emphasizing positive clutch elevation.</i>", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor("#6B7280"), alignment=1)))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Official Top 10 Bowlers Under Pressure (Dropdown Selections: Rank 1 to 10)", h2_style))
    top_bw = pd.read_csv('top_10_bowlers_under_pressure.csv')
    
    bw_table_data = [
        [
            Paragraph("<b>Rank</b>", table_header_style),
            Paragraph("<b>Bowler Name</b>", table_header_style),
            Paragraph("<b>HP Balls</b>", table_header_style),
            Paragraph("<b>HP Wkts</b>", table_header_style),
            Paragraph("<b>HP Econ</b>", table_header_style),
            Paragraph("<b>Base Econ</b>", table_header_style),
            Paragraph("<b>Runs Saved/6</b>", table_header_style),
            Paragraph("<b>HP SR</b>", table_header_style),
            Paragraph("<b>Dot %</b>", table_header_style),
            Paragraph("<b>Win %</b>", table_header_style),
            Paragraph("<b>Rating</b>", table_header_style)
        ]
    ]
    for _, r in top_bw.iterrows():
        bw_table_data.append([
            Paragraph(f"<b>{int(r['rank'])}</b>", table_cell_style),
            Paragraph(f"<b>{r['bowler_name']}</b>", table_cell_left),
            Paragraph(f"{int(r['hp_balls'])}", table_cell_style),
            Paragraph(f"{int(r['hp_wickets'])}", table_cell_style),
            Paragraph(f"<b>{r['hp_econ']:.2f}</b>", table_cell_style),
            Paragraph(f"{r['lp_econ']:.2f}", table_cell_style),
            Paragraph(f"<b>+{r['hp_rsae6_w']:.2f}</b>", table_cell_style),
            Paragraph(f"{r['hp_sr']:.1f}", table_cell_style),
            Paragraph(f"{r['hp_dot_pct']:.1f}%", table_cell_style),
            Paragraph(f"{r['positive_impact_pct']:.1f}%", table_cell_style),
            Paragraph(f"<b>{r['rating']:.2f}</b>", table_cell_style),
        ])

    t_bowl = Table(bw_table_data, colWidths=[24, 105, 38, 38, 42, 42, 54, 38, 38, 38, 47])
    t_bowl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_bowl)
    story.append(Spacer(1, 8))

    if os.path.exists('visualizations/top_10_bowlers_economy.png'):
        story.append(Image('visualizations/top_10_bowlers_economy.png', width=6.8*inch, height=2.4*inch))
        story.append(Paragraph("<i>Figure 3: Top 10 Bowlers High-Pressure Economy vs Baseline, highlighting net runs saved per over.</i>", ParagraphStyle('Cap', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor("#6B7280"), alignment=1)))

    story.append(PageBreak())

    # PAGE 4: Player Dossiers Part 1
    story.append(Paragraph("5. Detailed Tactical Dossiers for Top Selections", h1_style))
    story.append(Paragraph(
        "<b>Rank 1 Batter — Babar Azam (Rating: 89.37):</b> Contrary to public perception of anchor play, Babar's numbers in genuine high-pressure match situations (PI ≥ 65) are transcendent. He records an astonishing 219.57 HP strike rate (compared to 126.03 baseline, a clutch delta of +93.53 SR!), averaging 67.33 with an ultra-low 13.04% dot ball rate across 92 pressure balls. He delivered a positive net impact in 88.9% of pressure matches.<br/>"
        "<b>Rank 2 Batter — Suryakumar Yadav (Rating: 84.75):</b> The gold standard of sustained volume and lethality. Over 426 high-pressure balls in IPL and international cricket, SKY strikes at 215.49 (+57.84 delta over 157.65 baseline). Over 34.2% of his high-pressure deliveries result in boundaries (one boundary every 2.9 balls). In 74.4% of games, his high-pressure batting produced a game-winning run contribution.<br/>"
        "<b>Rank 3 Batter — Najibullah Zadran (Rating: 75.38):</b> Afghanistan's premier crisis manager elevates from a modest 109.18 baseline SR to 197.94 under pressure (+88.76 SR delta), averaging 48.00 with 81.8% match consistency.<br/>"
        "<b>Rank 4 Batter — Tristan Stubbs (Rating: 73.24):</b> A prototype modern 360-degree death specialist. Across 489 pressure deliveries, Stubbs boasts an elite 183.03 HP SR (+61.03 delta) and 38.91 average, maintaining a tiny 22.09% dot rate against elite death bowling.<br/>"
        "<b>Rank 5 Batter — Rishabh Pant (Rating: 73.06):</b> Rebounds with remarkable clutch conviction. Strikes at exactly 200.00 under pressure (+73.03 delta over 126.97 baseline), with 31.02% boundary hitting and 72.0% positive match rate.<br/>"
        "<b>Rank 6 Batter — Namboori Tilak Varma (Rating: 72.57):</b> Faced the largest high-pressure sample in the entire dataset (634 balls, 1178 runs). Demonstrates uncanny temperament, striking at 185.80 (+57.67 delta) with a 36.81 average and 64.4% positive impact rate.<br/>"
        "<b>Rank 7 Batter — Naman Dhir (Rating: 69.53):</b> The emerging breakout talent of 2024–2026. Across 199 pressure balls, strikes at 205.03 (+54.90 delta) with 31.16% boundaries, providing immense auction utility.<br/>"
        "<b>Rank 8 Batter — Matthew Wade (Rating: 69.43):</b> Veteran finishing masterclass. Strikes at 165.45 under pressure (+50.06 delta) while averaging an incredible 63.20 per dismissal.<br/>"
        "<b>Rank 9 Batter — Rovman Powell (Rating: 68.53):</b> Rajasthan Royals' trusted enforcer. Over 572 high-pressure balls, Powell scored 1061 runs at 185.49 SR (+60.77 delta), clearing ropes on 26.4% of balls.<br/>"
        "<b>Rank 10 Batter — Glenn Phillips (Rating: 68.42):</b> Dynamic multi-dimensional finisher with 204.59 HP SR (+70.15 delta) and 27.06% boundaries.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Rank 1 Bowler — Sunil Narine (Rating: 97.05):</b> The ultimate pressure strangler. Across 310 high-pressure balls in the IPL, Narine boasts an unbelievable <b>5.92 Economy Rate</b> (saving +3.78 runs per over vs expectation), taking 24 wickets at a 12.92 strike rate with 44.19% dots. His economy actually improves under pressure (6.97 baseline vs 5.92 HP). In 90.7% of pressure matches, Narine delivered a positive net run-suppression value.<br/>"
        "<b>Rank 2 Bowler — Mohammad Nawaz (Rating: 95.86):</b> Phenomenal left-arm control in tight chokes. Across 124 HP balls, concedes just 4.59 rpo (+3.73 runs saved/over) with a blistering 8.86 bowling strike rate, 50.81% dot rate, and 93.3% match positive rate.<br/>"
        "<b>Rank 3 Bowler — Abrar Ahmed (Rating: 90.89):</b> Mystery leg-spin execution. Across 204 HP balls, concedes 5.06 rpo with an 11.33 strike rate and 48.04% dots (88.0% consistency).<br/>"
        "<b>Rank 4 Bowler — Sufiyan Muqeem (Rating: 90.45):</b> Left-arm wrist spin prodigy. 4.84 HP economy and 61.24% dot balls across 129 HP deliveries (92.9% consistency).<br/>"
        "<b>Rank 5 Bowler — Umran Malik (Rating: 86.59):</b> Pure strike enforcer. Under high pressure, Umran's economy drops dramatically from 9.73 down to 7.03 rpo (+2.70 improvement!), while striking every <b>7.88 balls</b> (17 wickets in 134 HP balls) with 52.24% dot balls.<br/>"
        "<b>Rank 6 Bowler — Matheesha Pathirana (Rating: 80.04):</b> The premier death-overs pace weapon. Delivered an extraordinary 560 high-pressure balls (taking <b>50 wickets</b>!) with a 7.71 economy in an IPL environment where death expectation is 9.70, striking at 11.20 balls per wicket with 80.5% match consistency.<br/>"
        "<b>Rank 7 Bowler — Mitchell Santner (Rating: 75.48):</b> Elite accuracy. 6.77 HP economy across 288 balls, saving 2.07 runs/over with 13.71 strike rate.<br/>"
        "<b>Rank 8 Bowler — Shadab Khan (Rating: 75.41):</b> Middle/death overs leg-spin weapon. Concedes 6.54 HP rpo (12.00 strike rate, 41.67% dots).<br/>"
        "<b>Rank 9 Bowler — Spencer Johnson (Rating: 73.95):</b> Left-arm high-pace execution. 7.50 HP economy (+1.67 runs saved/over, 10.67 SR, 92.3% positive match rate).<br/>"
        "<b>Rank 10 Bowler — Kuldeep Yadav (Rating: 73.70):</b> India's premier wrist-spinner. 438 HP balls, 34 wickets, 7.90 HP economy, 12.88 strike rate, 38.13% dots.",
        body_style
    ))

    story.append(PageBreak())

    # PAGE 5: Section 6 & Final Assurance
    story.append(Paragraph("6. Reliability, Consistency Checks & Model Limitations", h1_style))
    story.append(Paragraph(
        "• <b>Match Consistency Verification:</b> Every player in our Top 10 boasts a <i>Positive Match Contribution Rate</i> exceeding 50% (and averaging 70–93%), confirming that their ratings reflect repeatable, game-in game-out reliability rather than one outlier performance.<br/>"
        "• <b>Opposition Breadth:</b> All top 10 bowlers and batters faced at least 8 to 16 distinct opposition franchises/nations under pressure, proving cross-opponent robustness.<br/>"
        "• <b>Innings Distribution:</b> Top batters showed strong balance across target chasing (Innings 2) and target setting / crisis management (Innings 1). For example, Tilak Varma recorded 382 balls in Innings 1 and 252 balls in Innings 2; Suryakumar Yadav faced 248 balls in Innings 1 and 178 balls in Innings 2.<br/>"
        "• <b>Known Model Limitations:</b> (1) <i>Tracking Absence:</i> The supplied dataset lacks Hawk-Eye ball tracking (pitch coordinates, release height, deviation), so bowling ratings measure outcome execution rather than pitch execution; (2) <i>Fielding Noise:</i> Dropped catches and misfields inevitably inject slight variance into bowler runs and batter dismissals; and (3) <i>Sample Asymmetry:</i> High-volume IPL veterans (Pathirana, Narine, SKY, Tilak) carry tighter posterior credible intervals than emerging talents (Spencer Johnson, Naman Dhir), although our Bayesian shrinkage explicitly penalizes small-sample variance.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("7. Franchise Strategy & Auction Recommendations for Rajasthan Royals", h1_style))
    story.append(Paragraph(
        "From an auction strategy and roster construction perspective, these empirical findings offer actionable intelligence for the Rajasthan Royals management:<br/>"
        "• <b>Death Bowling Asset Priority:</b> Matheesha Pathirana (50 wickets, 7.71 Econ in death-heavy pressure) and Spencer Johnson (left-arm pace, 7.50 Econ) represent tier-1 pace targets to complement existing attack structures.<br/>"
        "• <b>Middle-Overs Pressure Choke:</b> Sunil Narine (5.92 Econ under pressure) and Mitchell Santner (6.77 Econ) prove that elite spin is the most reliable mechanism to suppress high-pressure chases.<br/>"
        "• <b>Finishers with High Clutch Deltas:</b> Players like Tristan Stubbs (+61.0 ΔSR), Rovman Powell (+60.8 ΔSR), and Naman Dhir (+54.9 ΔSR) demonstrate the psychological resilience to accelerate when match pressure peaks.<br/>"
        "• <b>Retention Validation:</b> Rovman Powell's top-10 ranking (Rating 68.53, 572 pressure balls) strongly vindicates his strategic value to the Royals' finishing core.",
        body_style
    ))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=8))
    story.append(Paragraph("<b>Submission Assurance:</b> All 20 player names in this report match verbatim with <code>competition_team_player_mapping.csv</code> and are directly selectable via the Unstop dropdown fields. Prepared by the Senior Sports Data Scientist & Auction Strategy Consultant for Rajasthan Royals.", ParagraphStyle('SignOff', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor("#4B5563"))))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Refined PDF Report generated successfully: {filename}")

if __name__ == '__main__':
    build_pdf_report()
