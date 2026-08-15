import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from docx import Document
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

# ============================================================
# SIMON ORIGIN TRANSFORMATION - PERSONAL PLAN GENERATOR
# ============================================================
# Purpose:
#   YOU collect client information.
#   This private Telegram bot asks you the questions, calculates
#   calories/macros, fills your two DOCX templates, converts them
#   to PDF, and sends both PDFs back to YOU.
#
# Files required beside this script:
#   1. Calorie_Macro_Calculator.xlsx
#   2. 30-Day_Workout_Blueprint_TEMPLATE.docx
#   3. 30-Day_Nutrition_Blueprint_TEMPLATE.docx
#
# Environment variables:
#   BOT_TOKEN=your_telegram_bot_token
#   ADMIN_ID=your_telegram_user_id
#
# Optional:
#   OUTPUT_DIR=generated_plans
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CALCULATOR_FILE = BASE_DIR / "Calorie_Macro_Calculator.xlsx"
WORKOUT_TEMPLATE = BASE_DIR / "30-Day_Workout_Blueprint_TEMPLATE.docx"
NUTRITION_TEMPLATE = BASE_DIR / "30-Day_Nutrition_Blueprint_TEMPLATE.docx"
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "generated_plans")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")
if not ADMIN_ID_RAW.isdigit():
    raise RuntimeError("ADMIN_ID environment variable must be your numeric Telegram user ID.")
ADMIN_ID = int(ADMIN_ID_RAW)

# ------------------------------------------------------------
# 1. ADMIN CHECK
# ------------------------------------------------------------

def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == ADMIN_ID)

async def deny(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text("⛔ This is a private coaching/admin tool.")

# ------------------------------------------------------------
# 2. READ THE REFERENCE VALUES FROM YOUR EXCEL FILE
# ------------------------------------------------------------

def load_calculator_reference():
    if not CALCULATOR_FILE.exists():
        raise FileNotFoundError(f"Missing: {CALCULATOR_FILE.name}")

    wb = load_workbook(CALCULATOR_FILE, data_only=True)
    ws = wb["Calculator"]

    activity = {}
    for row in range(9, 13):
        name = ws[f"E{row}"].value
        multiplier = ws[f"F{row}"].value
        if name and multiplier:
            activity[str(name).strip()] = float(multiplier)

    goals = {}
    for row in range(9, 12):
        name = ws[f"G{row}"].value
        adjustment = ws[f"H{row}"].value
        if name is not None and adjustment is not None:
            goals[str(name).strip()] = float(adjustment)

    return activity, goals

ACTIVITY_MULTIPLIERS, GOAL_ADJUSTMENTS = load_calculator_reference()

# ------------------------------------------------------------
# 3. EXACT CALCULATION LOGIC FROM YOUR EXCEL
# ------------------------------------------------------------

def calculate_macros(data):
    gender = data["gender"].strip().lower()
    age = float(data["age"])
    height = float(data["height"])
    weight = float(data["weight"])
    activity = data["activity"]
    goal = data["goal"]

    # Matches your spreadsheet's Mifflin-St Jeor formula.
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    if activity not in ACTIVITY_MULTIPLIERS:
        raise ValueError(f"Unknown activity level: {activity}")
    if goal not in GOAL_ADJUSTMENTS:
        raise ValueError(f"Unknown goal: {goal}")

    tdee = bmr * ACTIVITY_MULTIPLIERS[activity]
    calories = tdee * (1 + GOAL_ADJUSTMENTS[goal])
    weekly_calories = calories * 7

    # Matches spreadsheet:
    # Protein = 2.0 g/kg
    # Fat = 25% of calories / 9
    # Carbs = remaining calories / 4
    protein = weight * 2.0
    protein_calories = protein * 4
    fats = (calories * 0.25) / 9
    fat_calories = fats * 9
    carbs = (calories - protein_calories - fat_calories) / 4
    water = weight * 0.05

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": round(calories),
        "weekly_calories": round(weekly_calories),
        "protein": round(protein),
        "protein_calories": round(protein_calories),
        "fats": round(fats),
        "fat_calories": round(fat_calories),
        "carbs": round(carbs),
        "water": round(water, 1),
    }

# ------------------------------------------------------------
# 4. EXERCISE LIBRARY
# ------------------------------------------------------------
# These exercise selections are the automation layer we add to
# your template. They are not taken from the uploaded template,
# because the template only contains [Exercise] placeholders.
# Review generated plans before sending to clients.

GYM_PLANS = {
    "Beginner": [
        [
            ("Machine Chest Press / የደረት ማሽን", "3", "8-12", "90s", "Controlled reps / በቁጥጥር"),
            ("Lat Pulldown / ላት ፑልዳውን", "3", "8-12", "90s", "Full range / ሙሉ ክልል"),
            ("Seated Cable Row / ሲቲድ ኬብል ሮ", "3", "10-12", "90s", "Neutral spine / ጀርባ ቀጥ"),
            ("Dumbbell Shoulder Press / ዳምቤል የትከሻ ፕሬስ", "2", "10-12", "75s", "Light-moderate load"),
            ("Cable Triceps Pressdown / ትራይሴፕስ", "2", "12-15", "60s", "Smooth movement"),
        ],
        [
            ("Goblet Squat / ጎብሌት ስኳት", "3", "8-12", "90s", "Controlled depth"),
            ("Romanian Deadlift / ሮማኒያን ዴድሊፍት", "3", "8-12", "90s", "Hinge at hips"),
            ("Leg Press / ሌግ ፕሬስ", "3", "10-12", "90s", "Do not lock knees"),
            ("Standing Calf Raise / የእግር ጫፍ", "3", "12-15", "60s", "Full range"),
            ("Dead Bug / ዴድ ባግ", "3", "8-12/side", "45s", "Brace core"),
        ],
        [
            ("Brisk Walk / ፈጣን መራመድ", "1", "20-30 min", "—", "Easy-moderate pace"),
            ("Cat-Cow / ካት-ካው", "2", "8-10", "30s", "Gentle mobility"),
            ("Hip Flexor Stretch / የዳሌ መዘርጋት", "2", "30s/side", "20s", "Gentle stretch"),
            ("Thoracic Rotation / የላይኛው ጀርባ", "2", "8/side", "30s", "Slow movement"),
            ("Child's Pose / የልጅ አቀማመጥ", "2", "30-45s", "20s", "Relaxed breathing"),
        ],
        [
            ("Incline Dumbbell Press / ኢንክላይን ዳምቤል", "3", "8-12", "90s", "Controlled"),
            ("Dumbbell Lateral Raise / የትከሻ ጎን", "3", "12-15", "60s", "Light weight"),
            ("Cable Chest Fly / የደረት ፍላይ", "2", "10-15", "60s", "Do not over-stretch"),
            ("Rope Triceps Pressdown / ትራይሴፕስ", "3", "10-15", "60s", "Full extension"),
            ("Plank / ፕላንክ", "3", "20-45s", "45s", "Neutral spine"),
        ],
        [
            ("Assisted Pull-Up / የተረዳ ፑል አፕ", "3", "6-10", "90s", "Controlled"),
            ("Seated Cable Row / ሲቲድ ሮ", "3", "8-12", "90s", "Squeeze back"),
            ("Dumbbell Curl / ቢሴፕስ ከርል", "3", "10-15", "60s", "No swinging"),
            ("Face Pull / ፌስ ፑል", "3", "12-15", "60s", "Shoulder control"),
            ("Back Extension / የጀርባ ኤክስቴንሽን", "2", "10-15", "60s", "Neutral spine"),
        ],
        [
            ("Leg Press / ሌግ ፕሬስ", "3", "10-12", "90s", "Controlled"),
            ("Dumbbell Romanian Deadlift / ዳምቤል RDL", "3", "8-12", "90s", "Hips back"),
            ("Walking Lunge / የመራመጃ ላንጅ", "2", "10/leg", "75s", "Stable steps"),
            ("Leg Curl / ሌግ ከርል", "3", "10-15", "60s", "Controlled"),
            ("Calf Raise / ካልፍ ሬዝ", "3", "12-15", "60s", "Full range"),
        ],
        [
            ("Rest / እረፍት", "—", "—", "—", "Optional easy walk"),
            ("Easy Walk / ቀላል መራመድ", "1", "15-30 min", "—", "Optional"),
            ("Gentle Stretch / ቀላል መዘርጋት", "1", "5-10 min", "—", "Optional"),
            ("Breathing / የመተንፈስ ልምምድ", "1", "3-5 min", "—", "Relax"),
            ("Recovery / ማገገሚያ", "—", "—", "—", "Prioritize sleep"),
        ],
    ]
}

# Intermediate/advanced versions use the same structure but slightly
# higher volume. This keeps the template stable and lets YOU review it.
def make_level_plan(level):
    base = GYM_PLANS["Beginner"]
    if level == "Beginner":
        return base
    multiplier = 1 if level == "Intermediate" else 2
    out = []
    for day in base:
        new_day = []
        for ex in day:
            name, sets, reps, rest, notes = ex
            if sets.isdigit() and name not in ("Rest / እረፍት",):
                sets = str(int(sets) + multiplier)
            new_day.append((name, sets, reps, rest, notes))
        out.append(new_day)
    return out

# Home plan: bodyweight/dumbbell-friendly. If client has no equipment,
# the exercises are bodyweight versions.
HOME_PLANS = {
    "Beginner": [
        [("Incline Push-Up / ኢንክላይን ፑሽ አፕ","3","8-15","60s","Use wall/table if needed"),
         ("Backpack Row / ቦርሳ ሮ","3","10-15","60s","Controlled"),
         ("Bodyweight Squat / የሰውነት ስኳት","3","10-15","60s","Knees track toes"),
         ("Glute Bridge / ግሉት ብሪጅ","3","12-15","60s","Squeeze glutes"),
         ("Plank / ፕላንክ","3","20-40s","45s","Brace core")],
        [("Bodyweight Squat / ስኳት","3","10-15","60s","Controlled"),
         ("Reverse Lunge / ሪቨርስ ላንጅ","3","8-12/leg","60s","Stable"),
         ("Glute Bridge / ግሉት ብሪጅ","3","12-15","60s","Pause at top"),
         ("Calf Raise / ካልፍ ሬዝ","3","15-20","45s","Full range"),
         ("Dead Bug / ዴድ ባግ","3","8-12/side","45s","Brace core")],
        [("Brisk Walk / ፈጣን መራመድ","1","20-30 min","—","Easy-moderate pace"),
         ("Cat-Cow / ካት-ካው","2","8-10","30s","Gentle"),
         ("Hip Flexor Stretch / የዳሌ መዘርጋት","2","30s/side","20s","Gentle"),
         ("Thoracic Rotation / የላይኛው ጀርባ","2","8/side","30s","Slow"),
         ("Child's Pose / የልጅ አቀማመጥ","2","30-45s","20s","Relax")],
        [("Push-Up / ፑሽ አፕ","3","8-15","60s","Modify as needed"),
         ("Pike Push-Up / ፓይክ ፑሽ አፕ","3","6-12","60s","Controlled"),
         ("Backpack Row / ቦርሳ ሮ","3","10-15","60s","Pull to ribs"),
         ("Chair Triceps Dip / ትራይሴፕስ","2","8-12","60s","Stable chair"),
         ("Plank / ፕላንክ","3","20-45s","45s","Neutral spine")],
        [("Backpack Row / ቦርሳ ሮ","3","10-15","60s","Controlled"),
         ("Reverse Snow Angel / ሪቨርስ ስኖ አንጀል","3","10-15","45s","Slow"),
         ("Backpack Curl / ቦርሳ ከርል","2","10-15","60s","No swinging"),
         ("Bird Dog / በርድ ዶግ","3","8-12/side","45s","Stable hips"),
         ("Superman / ሱፐርማን","2","8-12","45s","Gentle range")],
        [("Bodyweight Squat / ስኳት","3","10-15","60s","Controlled"),
         ("Reverse Lunge / ሪቨርስ ላንጅ","3","8-12/leg","60s","Stable"),
         ("Single-Leg Glute Bridge / አንድ እግር ግሉት","2","8-12/leg","60s","Control"),
         ("Calf Raise / ካልፍ ሬዝ","3","15-20","45s","Full range"),
         ("Wall Sit / ዎል ሲት","2","30-45s","45s","Comfortable depth")],
        [("Rest / እረፍት","—","—","—","Optional easy walk"),
         ("Easy Walk / ቀላል መራመድ","1","15-30 min","—","Optional"),
         ("Gentle Stretch / ቀላል መዘርጋት","1","5-10 min","—","Optional"),
         ("Breathing / መተንፈስ","1","3-5 min","—","Relax"),
         ("Recovery / ማገገሚያ","—","—","—","Prioritize sleep")],
    ]
}

# ------------------------------------------------------------
# 5. SIMPLE MEAL LIBRARY
# ------------------------------------------------------------
# The template itself contains [Add food] placeholders, so the exact
# foods are not specified by the uploaded source. These are practical
# starter suggestions. YOU should review substitutions, portions,
# allergies and cultural preferences before sending.

MEAL_LIBRARY = [
    "Eggs + oats + banana / እንቁላል + ኦትስ + ሙዝ",
    "Injera + shiro + salad / እንጀራ + ሽሮ + ሰላጣ",
    "Chicken + rice + vegetables / ዶሮ + ሩዝ + አትክልት",
    "Lentils + injera + vegetables / ምስር + እንጀራ + አትክልት",
    "Eggs + injera + vegetables / እንቁላል + እንጀራ + አትክልት",
    "Fish + potatoes + salad / ዓሳ + ድንች + ሰላጣ",
    "Beef + rice + vegetables / ስጋ + ሩዝ + አትክልት",
    "Ergo/yogurt + fruit + oats / እርጎ + ፍራፍሬ + ኦትስ",
]

MEAL_PATTERNS = [
    [0, 2, 1, 7],
    [4, 5, 3, 7],
    [0, 6, 3, 7],
    [1, 2, 5, 7],
    [4, 2, 3, 7],
    [0, 5, 1, 7],
    [4, 6, 3, 7],
]

DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS_AM = ["ሰኞ", "ማክሰኞ", "ረቡዕ", "ሐሙስ", "ዓርብ", "ቅዳሜ", "እሁድ"]

# ------------------------------------------------------------
# 6. DOCX PLACEHOLDER HELPERS
# ------------------------------------------------------------

def replace_text_in_paragraph(paragraph, replacements):
    for old, new in replacements.items():
        if old in paragraph.text:
            # Rebuild the paragraph as one run. This is safest for
            # placeholders, but is only used where the whole cell/paragraph
            # is a placeholder. Template formatting should otherwise remain.
            text = paragraph.text.replace(old, str(new))
            for run in paragraph.runs:
                run.text = ""
            if paragraph.runs:
                paragraph.runs[0].text = text
            else:
                paragraph.add_run(text)


def replace_everywhere(doc, replacements):
    # Normal paragraphs
    for p in doc.paragraphs:
        replace_text_in_paragraph(p, replacements)

    # Tables, including nested tables.
    def process_table(table):
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_text_in_paragraph(p, replacements)
                for nested in cell.tables:
                    process_table(nested)

    for table in doc.tables:
        process_table(table)

    # Headers/footers
    for section in doc.sections:
        for container in (section.header, section.footer):
            for p in container.paragraphs:
                replace_text_in_paragraph(p, replacements)
            for table in container.tables:
                process_table(table)


def set_cell_text(cell, text):
    # Preserve the cell's existing paragraph/table structure.
    p = cell.paragraphs[0]
    for run in p.runs:
        run.text = ""
    if p.runs:
        p.runs[0].text = str(text)
    else:
        p.add_run(str(text))


def fill_client_snapshot(table, values):
    # Table 1 in both supplied templates follows the same label/value layout.
    for row in table.rows:
        if len(row.cells) < 2:
            continue
        label = row.cells[0].text.lower()
        value = None
        if "full name" in label or "ሙሉ ስም" in label:
            value = values.get("name")
        elif "gender" in label or "ጾታ" in label:
            value = values.get("gender")
        elif "age" in label or "እድሜ" in label:
            value = values.get("age")
        elif "height" in label or "ቁመት" in label:
            value = f"{values.get('height')} cm"
        elif "weight" in label or "ክብደት" in label:
            value = f"{values.get('weight')} kg"
        elif "primary goal" in label or "ዋና ግብ" in label:
            value = values.get("goal")
        elif "activity level" in label or "የእንቅስቃሴ" in label:
            value = values.get("activity")
        elif "fitness level" in label or "ብቃት" in label:
            value = values.get("experience")
        elif "training experience" in label or "ልምድ" in label:
            value = values.get("experience")
        elif "equipment" in label or "መሳሪያ" in label:
            value = values.get("equipment")
        elif "main obstacle" in label or "ተግዳሮት" in label:
            value = values.get("obstacle", "Consistency")
        elif "restriction" in label or "allerg" in label or "ገደቦች" in label or "አለርጂ" in label:
            value = values.get("restrictions", "None")
        elif "health" in label or "injur" in label or "ጤና" in label or "ጉዳት" in label:
            value = values.get("injuries", "None")
        elif "eating pattern" in label or "አመጋገብ ስርዓት" in label:
            value = values.get("meals", "4 meals/day")
        elif "training preference" in label or "ምርጫ" in label:
            value = values.get("training_preference", "General Fitness")

        if value is not None:
            set_cell_text(row.cells[1], value)

# ------------------------------------------------------------
# 7. FILL NUTRITION TEMPLATE
# ------------------------------------------------------------

def fill_nutrition_doc(data, macros, output_docx):
    doc = Document(NUTRITION_TEMPLATE)

    replacements = {
        "[INSERT CLIENT NAME]": data["name"],
        "[INSERT GENDER]": data["gender"],
        "[INSERT AGE]": data["age"],
        "[INSERT HEIGHT]": data["height"],
        "[INSERT WEIGHT]": data["weight"],
        "[Fat Loss / Muscle Gain / Maintenance]": data["goal"],
        "[Sedentary / Lightly Active / Moderate / Very Active]": data["activity"],
        "[Beginner / Intermediate / Advanced]": data["experience"],
        "[Consistency]": data.get("obstacle", "Consistency"),
        "[INSERT RESTRICTIONS or 'None']": data.get("restrictions", "None"),
        "[INSERT INJURIES or 'None']": data.get("injuries", "None"),
        "[4 meals/day]": data.get("meals", "4 meals/day"),
        "[CALCULATED TARGET]": macros["calories"],
        "[XXX]": macros["protein"],
        "[XX]": macros["fats"],
        "[X.X]": macros["water"],
        "[DAILY TARGET x 7]": macros["weekly_calories"],
    }
    replace_everywhere(doc, replacements)

    # Snapshot is more reliable as a direct table update.
    if len(doc.tables) > 1:
        fill_client_snapshot(doc.tables[1], data)

    # Calorie/macro table.
    if len(doc.tables) > 2:
        t = doc.tables[2]
        values = [
            f"{macros['calories']:,} kcal / day",
            "Mifflin-St Jeor BMR × Activity Multiplier, adjusted for goal",
            f"{macros['protein']} g  (~2.0g/kg body weight)",
            f"{macros['carbs']} g  (periodized by training day)",
            f"{macros['fats']} g",
            f"{macros['water']} Liters",
            f"{macros['weekly_calories']:,} kcal / week",
        ]
        for i, value in enumerate(values):
            if i < len(t.rows) and len(t.rows[i].cells) > 1:
                set_cell_text(t.rows[i].cells[1], value)

    # 7-day meal matrix.
    if len(doc.tables) > 3:
        t = doc.tables[3]
        for day_index in range(7):
            row_index = day_index + 1
            if row_index >= len(t.rows):
                break
            pattern = MEAL_PATTERNS[day_index]
            for col, meal_index in enumerate(pattern, start=1):
                if col < len(t.rows[row_index].cells):
                    set_cell_text(t.rows[row_index].cells[col], MEAL_LIBRARY[meal_index])
            if len(t.rows[row_index].cells) >= 6:
                set_cell_text(
                    t.rows[row_index].cells[5],
                    f"{macros['calories']:,} / {macros['protein']}g"
                )

    doc.save(output_docx)

# ------------------------------------------------------------
# 8. FILL WORKOUT TEMPLATE
# ------------------------------------------------------------

def fill_workout_doc(data, output_docx):
    doc = Document(WORKOUT_TEMPLATE)

    replacements = {
        "[INSERT CLIENT NAME]": data["name"],
        "[INSERT GENDER]": data["gender"],
        "[INSERT AGE]": data["age"],
        "[INSERT HEIGHT]": data["height"],
        "[INSERT WEIGHT]": data["weight"],
        "[Fat Loss / Muscle Gain / Maintenance]": data["goal"],
        "[Beginner / Intermediate / Advanced]": data["experience"],
        "[Home / Gym / Both]": data["equipment"],
        "[Consistency]": data.get("obstacle", "Consistency"),
        "[INSERT INJURIES or 'None']": data.get("injuries", "None"),
        "[Strength / Fat Loss / General Fitness]": data.get("training_preference", "General Fitness"),
    }
    replace_everywhere(doc, replacements)

    if len(doc.tables) > 1:
        fill_client_snapshot(doc.tables[1], data)

    if len(doc.tables) > 3:
        level = data.get("experience", "Beginner")
        equipment = data.get("equipment", "Home")
        if equipment == "Gym":
            plan = make_level_plan(level)
        else:
            plan = HOME_PLANS["Beginner"]
            if level != "Beginner":
                # Add a small volume increase for higher experience.
                plan = make_level_plan_from_home(plan, level)

        # Tables 4-10 correspond to Day 1-Day 7 in the supplied template.
        for day_index in range(7):
            table_index = 4 + day_index
            if table_index >= len(doc.tables):
                break
            table = doc.tables[table_index]
            exercises = plan[day_index]
            for i, exercise in enumerate(exercises, start=1):
                if i >= len(table.rows):
                    break
                for col, value in enumerate(exercise):
                    if col < len(table.rows[i].cells):
                        set_cell_text(table.rows[i].cells[col], value)

    doc.save(output_docx)


def make_level_plan_from_home(base, level):
    add = 1 if level == "Intermediate" else 2
    out = []
    for day in base:
        nd = []
        for ex in day:
            name, sets, reps, rest, notes = ex
            if sets.isdigit() and "Rest /" not in name:
                sets = str(int(sets) + add)
            nd.append((name, sets, reps, rest, notes))
        out.append(nd)
    return out

# ------------------------------------------------------------
# 9. DOCX -> PDF
# ------------------------------------------------------------

def convert_to_pdf(docx_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if shutil.which("libreoffice"):
        command = [
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(output_dir), str(docx_path)
        ]
    elif shutil.which("soffice"):
        command = [
            "soffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(output_dir), str(docx_path)
        ]
    else:
        raise RuntimeError(
            "LibreOffice is not installed. Install LibreOffice on your server/PC."
        )

    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    pdf_path = output_dir / (Path(docx_path).stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"PDF conversion failed: {pdf_path}")
    return pdf_path

# ------------------------------------------------------------
# 10. GENERATE BOTH FILES
# ------------------------------------------------------------

def safe_filename(name):
    name = re.sub(r"[^A-Za-z0-9_\- ]+", "", name).strip().replace(" ", "_")
    return name or "Client"


def generate_client_package(data):
    macros = calculate_macros(data)
    client_folder = OUTPUT_DIR / f"{safe_filename(data['name'])}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    client_folder.mkdir(parents=True, exist_ok=True)

    workout_docx = client_folder / f"{safe_filename(data['name'])}_Workout_Blueprint.docx"
    nutrition_docx = client_folder / f"{safe_filename(data['name'])}_Nutrition_Blueprint.docx"

    fill_workout_doc(data, workout_docx)
    fill_nutrition_doc(data, macros, nutrition_docx)

    workout_pdf = convert_to_pdf(workout_docx, client_folder)
    nutrition_pdf = convert_to_pdf(nutrition_docx, client_folder)

    return macros, workout_pdf, nutrition_pdf

# ------------------------------------------------------------
# 11. TELEGRAM ADMIN WIZARD
# ------------------------------------------------------------

QUESTIONS = [
    ("name", "👤 Client full name?"),
    ("gender", "♂️/♀️ Gender? Reply: Male or Female"),
    ("age", "🎂 Age?"),
    ("height", "📏 Height in cm?"),
    ("weight", "⚖️ Weight in kg?"),
    ("goal", "🎯 Goal? Reply: Fat Loss, Muscle Gain, or Maintenance"),
    ("activity", "🏃 Activity level? Reply: Sedentary, Lightly Active, Moderate, or Very Active"),
    ("experience", "🏋️ Training experience? Reply: Beginner, Intermediate, or Advanced"),
    ("equipment", "🏠 Equipment? Reply: Home or Gym"),
    ("training_preference", "💪 Training preference? Reply: Strength, Fat Loss, or General Fitness"),
    ("obstacle", "🧠 Main obstacle? Example: Consistency"),
    ("restrictions", "🍽️ Diet restrictions/allergies? Reply None if none."),
    ("injuries", "⚠️ Health/injuries? Reply None if none."),
    ("meals", "🍴 Meals per day? Usually 4. Reply with a number or '4 meals/day'."),
]


def normalize_choice(value, allowed):
    clean = value.strip().lower()
    for item in allowed:
        if clean == item.lower():
            return item
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    context.user_data.clear()
    context.user_data["step"] = 0
    await update.message.reply_text(
        "🧑‍💻 SIMON ORIGIN PLAN GENERATOR\n\n"
        "This private tool will collect the client information, calculate the nutrition targets, "
        "fill your existing Workout + Nutrition templates, convert them to PDF, and send both files to you.\n\n"
        "Let's start.\n\n" + QUESTIONS[0][1]
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    context.user_data.clear()
    await update.message.reply_text("❌ Generation cancelled. Use /generate to start again.")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)
    await update.message.reply_text(
        "✅ Plan generator is online.\n\n"
        f"Excel: {'OK' if CALCULATOR_FILE.exists() else 'MISSING'}\n"
        f"Workout template: {'OK' if WORKOUT_TEMPLATE.exists() else 'MISSING'}\n"
        f"Nutrition template: {'OK' if NUTRITION_TEMPLATE.exists() else 'MISSING'}\n"
        f"LibreOffice: {'OK' if (shutil.which('libreoffice') or shutil.which('soffice')) else 'MISSING'}"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return await deny(update)

    if "step" not in context.user_data:
        await update.message.reply_text("Use /generate to create a new client plan.")
        return

    step = context.user_data["step"]
    key, _ = QUESTIONS[step]
    value = update.message.text.strip()

    # Validation
    if key == "age":
        try:
            n = int(value)
            if not 12 <= n <= 100:
                raise ValueError
            value = str(n)
        except ValueError:
            await update.message.reply_text("Please enter a valid age between 12 and 100.")
            return

    elif key == "height":
        try:
            n = float(value)
            if not 100 <= n <= 250:
                raise ValueError
            value = str(n).rstrip('0').rstrip('.') if '.' in str(n) else str(n)
        except ValueError:
            await update.message.reply_text("Please enter height in cm, e.g. 175.")
            return

    elif key == "weight":
        try:
            n = float(value)
            if not 30 <= n <= 300:
                raise ValueError
            value = str(n).rstrip('0').rstrip('.') if '.' in str(n) else str(n)
        except ValueError:
            await update.message.reply_text("Please enter weight in kg, e.g. 70.")
            return

    elif key == "gender":
        value = normalize_choice(value, ["Male", "Female"])
        if not value:
            await update.message.reply_text("Reply exactly: Male or Female")
            return

    elif key == "goal":
        value = normalize_choice(value, list(GOAL_ADJUSTMENTS.keys()))
        if not value:
            await update.message.reply_text("Reply: Fat Loss, Muscle Gain, or Maintenance")
            return

    elif key == "activity":
        value = normalize_choice(value, list(ACTIVITY_MULTIPLIERS.keys()))
        if not value:
            await update.message.reply_text(
                "Reply: Sedentary, Lightly Active, Moderate, or Very Active"
            )
            return

    elif key == "experience":
        value = normalize_choice(value, ["Beginner", "Intermediate", "Advanced"])
        if not value:
            await update.message.reply_text("Reply: Beginner, Intermediate, or Advanced")
            return

    elif key == "equipment":
        value = normalize_choice(value, ["Home", "Gym"])
        if not value:
            await update.message.reply_text("Reply: Home or Gym")
            return

    elif key == "training_preference":
        value = normalize_choice(value, ["Strength", "Fat Loss", "General Fitness"])
        if not value:
            await update.message.reply_text("Reply: Strength, Fat Loss, or General Fitness")
            return

    elif key == "meals":
        if value.isdigit():
            value = f"{value} meals/day"
        elif not value:
            value = "4 meals/day"

    context.user_data[key] = value
    context.user_data["step"] += 1

    next_step = context.user_data["step"]
    if next_step < len(QUESTIONS):
        await update.message.reply_text(QUESTIONS[next_step][1])
        return

    # Complete
    data = {k: context.user_data[k] for k, _ in QUESTIONS}
    await update.message.reply_text("⏳ Building both personalized PDFs... Please wait.")

    try:
        macros, workout_pdf, nutrition_pdf = generate_client_package(data)

        await update.message.reply_text(
            "✅ DONE\n\n"
            f"Client: {data['name']}\n"
            f"Calories: {macros['calories']:,} kcal/day\n"
            f"Protein: {macros['protein']} g\n"
            f"Carbs: {macros['carbs']} g\n"
            f"Fat: {macros['fats']} g\n"
            f"Water: {macros['water']} L\n\n"
            "Review the PDFs before sending to the client."
        )

        with open(workout_pdf, "rb") as f:
            await update.message.reply_document(
                document=f,
                caption=f"🏋️ {data['name']} — 30-Day Workout Blueprint"
            )

        with open(nutrition_pdf, "rb") as f:
            await update.message.reply_document(
                document=f,
                caption=f"🍽️ {data['name']} — 30-Day Nutrition Blueprint"
            )

    except Exception as e:
        await update.message.reply_text(
            "❌ Generation failed.\n\n"
            f"Error: {e}\n\n"
            "Use /status to check your files and LibreOffice installation."
        )
    finally:
        context.user_data.clear()

# ------------------------------------------------------------
# 12. MAIN
# ------------------------------------------------------------

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Simon Origin Plan Generator is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
