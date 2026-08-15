# -*- coding: utf-8 -*-
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.lib.units import mm

from pdf_render import (
    get_styles, build_header, build_snapshot_table, section_title,
    footer_note, make_doc, TABLE_HEADER_STYLE, mixed_font
)
from calculations import calc_targets
from meal_builder import build_meal_plan

PILLARS = [
    ("Macro Precision", "የፕሮቲን ትክክለኛነት",
     "Hit daily protein targets within +/- 5g. Protein drives muscle protein synthesis and keeps satiety high."),
    ("Nutrient Periodization", "የተመጣጠነ አመጋገብ",
     "Eat higher carbohydrates on heavy training days and lower carbohydrates on rest/recovery days."),
    ("Meal Timing & Frequency", "የምግብ ሰዓት እና ድግግሞሽ",
     "Spread protein evenly across 4 main feeding windows every 3-4 hours."),
    ("Bio-Available Local Foods", "የአካባቢ ምግቦች",
     "Utilize nutrient-dense local staples like Teff, Shiro, Misir, Eggs, and Ergo for optimal digestion."),
]

PROGRESSION_WEEKS = [
    ("Week 1 - Foundation", "1ኛ ሳምንት — መሰረት",
     "Baseline calories & macros as calculated. Focus on hitting targets +/- 5g protein, establishing meal timing habits."),
    ("Week 2 - Build", "2ኛ ሳምንት — ግንባታ",
     "Carbs +15-20g on training days only. Calories unchanged. Reassess hunger/energy."),
    ("Week 3 - Push", "3ኛ ሳምንት — ግስጋሴ",
     "Hold Week 2 targets. Tighten adherence — this week determines the reassessment outcome."),
    ("Week 4 - Deload / Reassess", "4ኛ ሳምንት — ማስተካከያ",
     "Calories -10% (deload), re-measure weight/tape Sunday, full check-in submitted, targets recalculated for next cycle."),
]


def generate_nutrition_pdf(assessment: dict, out_path: str) -> str:
    styles = get_styles()

    weight = float(assessment["weight_kg"])
    height = float(assessment["height_cm"])
    age = int(assessment["age"])
    targets = calc_targets(
        weight, height, age, assessment.get("gender", "male"),
        assessment.get("activity_level", "moderate"),
        assessment.get("primary_goal", "fat loss"),
    )
    meal_plan = build_meal_plan(assessment, targets)

    story = []
    story += build_header(
        styles, "30-Day Personalized Nutrition Blueprint",
        "የ30 ቀን የግል የአመጋገብ ዕቅድ",
        assessment.get("full_name", ""), assessment.get("date", ""),
    )

    story += [Paragraph("Client Snapshot", styles["section_en"]), Spacer(1, 3)]
    snapshot_rows = [
        ("Full Name", "ሙሉ ስም", assessment.get("full_name", "")),
        ("Gender", "ጾታ", assessment.get("gender", "")),
        ("Age", "እድሜ", assessment.get("age", "")),
        ("Height", "ቁመት", f"{height:g} cm"),
        ("Weight", "ክብደት", f"{weight:g} kg"),
        ("Primary Goal", "ዋና ግብ", assessment.get("primary_goal", "")),
        ("Activity Level", "የእንቅስቃሴ ደረጃ", assessment.get("activity_level", "")),
        ("Fitness Level", "የብቃት ደረጃ", assessment.get("training_experience", "")),
        ("Main Obstacle", "ዋና ተግዳሮት", assessment.get("main_obstacle", "Consistency")),
        ("Diet Restrictions / Allergies", "የአመጋገብ ገደቦች / አለርጂ", assessment.get("diet_restrictions", "None")),
        ("Health / Injuries", "የጤና ሁኔታ / ጉዳት", assessment.get("health_injuries", "None")),
        ("Eating Pattern", "የአመጋገብ ስርዓት", "4 meals/day"),
    ]
    story.append(build_snapshot_table(styles, snapshot_rows))

    story += section_title(styles, "1. Calorie & Macro Targets", "የካሎሪ እና ማክሮ ግቦች")
    story.append(Paragraph(
        "Your daily targets are calculated from your intake data using the Mifflin-St Jeor "
        "equation for basal metabolic rate, scaled by activity level, then adjusted for your "
        "primary goal. Hit these consistently and the plan works.", styles["body"]))
    target_rows = [
        ("Estimated Daily Calories", "የዕለት ካሎሪ ግምት", f"{targets['calories']:,} kcal / day"),
        ("Method", "ስሌት ዘዴ", "Mifflin-St Jeor BMR x Activity Multiplier, adjusted for goal"),
        ("Protein Target", "የፕሮቲን ግብ", f"{targets['protein_g']} g  (~2.0g/kg body weight)"),
        ("Carbohydrate Target", "የካርቦሃይድሬት ግብ", f"{targets['carbs_g']} g  (periodized by training day)"),
        ("Fat Target", "የስብ ግብ", f"{targets['fat_g']} g"),
        ("Daily Fluid Target", "የዕለት ውሃ ግብ", f"{targets['fluid_l']} Liters"),
        ("Weekly Calorie Total", "የሳምንት ጠቅላላ ካሎሪ", f"{targets['weekly_calories']:,} kcal / week"),
    ]
    story.append(Spacer(1, 4))
    story.append(build_snapshot_table(styles, target_rows))

    story += section_title(styles, "2. The 4 Pillars of Elite Nutrition", "አራት የአመጋገብ ምሰሶዎች")
    items = []
    for en, am, desc in PILLARS:
        items.append(ListItem(Paragraph(
            f'<font name="Helvetica-Bold">{en}:</font> {desc}<br/>'
            f'<font size="7.5" color="#777777">{mixed_font(am)}</font>',
            styles["cell_en"]), bulletColor="#B8860B"))
    story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=12, spaceAfter=6))

    story.append(PageBreak())
    story += section_title(styles, "3. Full 7-Day Meal Matrix", "የ7-ቀን ምግብ ሰንጠረዥ")
    story.append(Paragraph(
        "This matrix repeats weekly. Portions are sized to your calorie/protein targets above; "
        "adjust per the 4-week progression table below.", styles["body"]))
    story.append(Spacer(1, 4))

    meal_labels = ["Meal 1 (Breakfast)", "Meal 2 (Lunch)", "Meal 3 (Dinner)", "Meal 4 (Snack)"]
    for row in meal_plan["rows"]:
        story.append(Paragraph(mixed_font(
            f"{row['day_en']} / {row['day_am']}  —  "
            f"{row['kcal']:,} kcal / {row['protein']}g protein", bold=True),
            styles["section_en"]))
        table_rows = [[Paragraph(h, styles["header_cell"]) for h in ["Meal", "Foods (Amharic)", "kcal / protein"]]]
        for label, meal in zip(meal_labels, row["meals"]):
            items_markup = "<br/>".join(mixed_font(item) for item in meal["items"])
            table_rows.append([
                Paragraph(label, styles["cell_en_bold"]),
                Paragraph(items_markup, styles["cell_en"]),
                Paragraph(f"{meal['kcal']} kcal<br/>{meal['protein']}g protein", styles["cell_en"]),
            ])
        tbl = Table(table_rows, colWidths=[32 * mm, 96 * mm, 22 * mm], repeatRows=1)
        tbl.setStyle(TableStyle(TABLE_HEADER_STYLE))
        story.append(tbl)
        story.append(Spacer(1, 6))

    story.append(PageBreak())
    story += section_title(styles, "4. 4-Week Progression Plan", "የ4-ሳምንት ግስጋሴ ዕቅድ")
    prog_rows = [[Paragraph(mixed_font(h, bold=True), styles["header_cell"]) for h in ["Phase", "ደረጃ", "Adjustment / Focus"]]]
    for en, am, note in PROGRESSION_WEEKS:
        prog_rows.append([
            Paragraph(en, styles["cell_en_bold"]),
            Paragraph(mixed_font(am), styles["cell_am"]),
            Paragraph(note, styles["cell_en"]),
        ])
    prog_tbl = Table(prog_rows, colWidths=[42 * mm, 34 * mm, 74 * mm], repeatRows=1)
    prog_tbl.setStyle(TableStyle(TABLE_HEADER_STYLE))
    story.append(prog_tbl)

    story += footer_note(styles)

    doc = make_doc(out_path)
    doc.build(story)
    return out_path
