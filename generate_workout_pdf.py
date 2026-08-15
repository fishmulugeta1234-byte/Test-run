# -*- coding: utf-8 -*-
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import mm
from reportlab.lib import colors

from pdf_render import (
    get_styles, build_header, build_snapshot_table, section_title,
    footer_note, make_doc, TABLE_HEADER_STYLE, INK, GOLD, mixed_font
)
from workout_builder import build_workout_plan

PROGRESSION_WEEKS = [
    ("Week 1 - Foundation", "1ኛ ሳምንት — መሰረት",
     "Establish technique on all key lifts. Moderate load, focus on full range of motion."),
    ("Week 2 - Build", "2ኛ ሳምንት — ግንባታ",
     "+2.5-5kg on key lifts or +1-2 reps per set. Maintain form quality."),
    ("Week 3 - Push", "3ኛ ሳምንት — ግስጋሴ",
     "Peak volume/intensity of the cycle. Push toward rep or load PRs on key lifts."),
    ("Week 4 - Deload / Reassess", "4ኛ ሳምንት — ማስተካከያ",
     "Volume -40%, intensity moderate. Re-test key lifts, submit check-in, plan next cycle."),
]


def generate_workout_pdf(assessment: dict, out_path: str) -> str:
    styles = get_styles()
    plan = build_workout_plan(assessment)

    story = []
    story += build_header(
        styles, "30-Day Personalized Workout Blueprint",
        "የ30 ቀን የግል የልምምድ ዕቅድ",
        assessment.get("full_name", ""), assessment.get("date", ""),
    )

    story += [Paragraph("Client Snapshot", styles["section_en"]), Spacer(1, 3)]
    snapshot_rows = [
        ("Full Name", "ሙሉ ስም", assessment.get("full_name", "")),
        ("Gender", "ጾታ", assessment.get("gender", "")),
        ("Age", "እድሜ", assessment.get("age", "")),
        ("Height", "ቁመት", f"{assessment.get('height_cm', '')} cm"),
        ("Weight", "ክብደት", f"{assessment.get('weight_kg', '')} kg"),
        ("Primary Goal", "ዋና ግብ", assessment.get("primary_goal", "")),
        ("Training Experience", "የልምምድ ልምድ", assessment.get("training_experience", "")),
        ("Equipment Available", "ያለ መሳሪያ", assessment.get("equipment_available", "")),
        ("Main Obstacle", "ዋና ተግዳሮት", assessment.get("main_obstacle", "Consistency")),
        ("Health / Injuries", "የጤና ሁኔታ / ጉዳት", assessment.get("health_injuries", "None")),
        ("Training Preference", "የልምምድ ምርጫ", assessment.get("training_preference", "")),
    ]
    story.append(build_snapshot_table(styles, snapshot_rows))

    story += section_title(styles, "1. Training Targets & Structure", "የልምምድ ዒላማ እና ስርዓት")
    story.append(Paragraph(
        "Your training targets are built around your current ability, schedule, equipment, "
        "and primary goal. Train consistently, progress gradually, recover well.", styles["body"]))
    struct_rows = [
        ("Training Frequency", "የልምምድ ድግግሞሽ", plan["frequency"]),
        ("Session Length", "የክፍለ ጊዜ ርዝመት", plan["session_length"]),
        ("Primary Method", "ዋና ዘዴ", plan["scheme_summary"]),
        ("Warm-Up", "ማሞቂያ", "5-10 minutes before every session"),
    ]
    story.append(Spacer(1, 4))
    story.append(build_snapshot_table(styles, struct_rows))

    story += section_title(styles, "2. 7-Day Daily Training Program", "የ7-ቀን የዕለት የልምምድ መርሃ ግብር")
    story.append(Paragraph(
        "This program repeats weekly. Adjust load/volume per the 4-week progression table below.",
        styles["body"]))
    story.append(Spacer(1, 4))

    col_widths = [58 * mm, 14 * mm, 16 * mm, 16 * mm, 46 * mm]
    for day in plan["days"]:
        story.append(Paragraph(day["title_en"], styles["section_en"]))
        story.append(Paragraph(mixed_font(day["title_am"]), styles["section_am"]))
        header = [Paragraph(h, styles["header_cell"]) for h in
                  ["Exercise", "Sets", "Reps", "Rest", "Notes"]]
        rows = [header]
        for ex in day["exercises"]:
            rows.append([
                Paragraph(ex["name"], styles["cell_en"]),
                Paragraph(ex["sets"], styles["cell_en"]),
                Paragraph(ex["reps"], styles["cell_en"]),
                Paragraph(ex["rest"], styles["cell_en"]),
                Paragraph(ex["notes"], styles["cell_en"]),
            ])
        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(TABLE_HEADER_STYLE))
        story.append(tbl)
        story.append(Spacer(1, 6))

    story.append(PageBreak())
    story += section_title(styles, "3. 4-Week Progression Plan", "የ4-ሳምንት ግስጋሴ ዕቅድ")
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
