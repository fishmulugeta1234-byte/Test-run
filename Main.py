import os
import re
import logging
from pathlib import Path

from docxtpl import DocxTemplate
from openpyxl import load_workbook

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# EXACT FILENAMES FROM YOUR GITHUB REPOSITORY
WORKOUT_TEMPLATE = BASE_DIR / "Simon_30Day_Workout_Blueprint_Updated.docx"

NUTRITION_TEMPLATE = BASE_DIR / "Simon_30Day_Nutrition_Blueprint-1.docx"

CALCULATOR_FILE = BASE_DIR / "Simon_Calorie_Macro_Calculator.xlsx"

# Folder for temporary generated documents
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Telegram token from Render Environment Variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is missing. "
        "Add TELEGRAM_BOT_TOKEN in Render Environment Variables."
    )


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# CHECK REQUIRED FILES
# ============================================================

def check_required_files():

    required_files = [
        WORKOUT_TEMPLATE,
        NUTRITION_TEMPLATE,
        CALCULATOR_FILE,
    ]

    missing = []

    for file in required_files:

        if not file.exists():
            missing.append(file.name)

    if missing:

        raise FileNotFoundError(
            "Missing required files:\n"
            + "\n".join(missing)
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_filename(name):

    name = str(name).strip()

    name = re.sub(
        r'[<>:"/\\|?*]',
        "",
        name
    )

    name = re.sub(
        r"\s+",
        "_",
        name
    )

    if not name:
        name = "Client"

    return name


def parse_number(value, field_name):

    try:

        return float(
            str(value)
            .replace(",", "")
            .strip()
        )

    except Exception:

        raise ValueError(
            f"{field_name} must be a number."
        )


# ============================================================
# CALCULATE NUTRITION
# ============================================================

def calculate_macros(client_data):

    weight = parse_number(
        client_data["weight"],
        "Weight"
    )

    height = parse_number(
        client_data["height"],
        "Height"
    )

    age = parse_number(
        client_data["age"],
        "Age"
    )

    gender = client_data["gender"].lower().strip()

    activity = (
        client_data["activity_level"]
        .lower()
        .strip()
    )

    goal = (
        client_data["goal"]
        .lower()
        .strip()
    )

    # --------------------------------------------------------
    # Mifflin-St Jeor
    # --------------------------------------------------------

    if gender in [
        "male",
        "m",
        "man"
    ]:

        bmr = (
            (10 * weight)
            + (6.25 * height)
            - (5 * age)
            + 5
        )

    elif gender in [
        "female",
        "f",
        "woman"
    ]:

        bmr = (
            (10 * weight)
            + (6.25 * height)
            - (5 * age)
            - 161
        )

    else:

        bmr = (
            (10 * weight)
            + (6.25 * height)
            - (5 * age)
        )

    # --------------------------------------------------------
    # ACTIVITY MULTIPLIERS
    # --------------------------------------------------------

    activity_multipliers = {

        "sedentary": 1.20,

        "light": 1.375,

        "lightly active": 1.375,

        "moderate": 1.55,

        "moderately active": 1.55,

        "very active": 1.725,

        "extremely active": 1.90,
    }

    activity_multiplier = activity_multipliers.get(
        activity,
        1.55
    )

    # --------------------------------------------------------
    # MAINTENANCE CALORIES
    # --------------------------------------------------------

    maintenance_calories = (
        bmr * activity_multiplier
    )

    # --------------------------------------------------------
    # GOAL ADJUSTMENT
    # --------------------------------------------------------

    if (
        "fat loss" in goal
        or "weight loss" in goal
        or "lose" in goal
    ):

        calories = maintenance_calories * 0.85

    elif (
        "muscle gain" in goal
        or "gain" in goal
    ):

        calories = maintenance_calories * 1.10

    else:

        calories = maintenance_calories

    calories = round(calories)

    # --------------------------------------------------------
    # PROTEIN
    # --------------------------------------------------------

    protein = round(
        weight * 2.0
    )

    # --------------------------------------------------------
    # FAT
    # --------------------------------------------------------

    fats = round(
        weight * 0.9
    )

    # --------------------------------------------------------
    # CARBOHYDRATES
    # --------------------------------------------------------

    protein_calories = protein * 4

    fat_calories = fats * 9

    remaining_calories = (
        calories
        - protein_calories
        - fat_calories
    )

    carbs = round(
        max(remaining_calories, 0) / 4
    )

    # --------------------------------------------------------
    # WATER
    # --------------------------------------------------------

    water = round(
        weight * 0.035,
        1
    )

    # --------------------------------------------------------
    # WEEKLY CALORIES
    # --------------------------------------------------------

    weekly_calories = (
        calories * 7
    )

    return {

        "calories": calories,

        "protein": protein,

        "carbs": carbs,

        "fats": fats,

        "water": water,

        "weekly_calories": weekly_calories,

        "bmr": round(bmr),

        "maintenance_calories": round(
            maintenance_calories
        ),

        "activity_multiplier": activity_multiplier,
    }


# ============================================================
# UPDATE EXCEL CALCULATOR
# ============================================================

def update_calculator(
    client_data,
    macros
):

    try:

        workbook = load_workbook(
            CALCULATOR_FILE
        )

        if "Bot Calculator" in workbook.sheetnames:

            sheet = workbook[
                "Bot Calculator"
            ]

        else:

            sheet = workbook.create_sheet(
                "Bot Calculator",
                0
            )

        sheet["B3"] = float(
            client_data["weight"]
        )

        sheet["B4"] = float(
            macros["activity_multiplier"]
        )

        sheet["B5"] = macros["calories"]

        sheet["B6"] = macros["protein"]

        sheet["B7"] = macros["fats"]

        sheet["B8"] = macros["carbs"]

        client_name = safe_filename(
            client_data["name"]
        )

        output_file = (
            OUTPUT_DIR
            / f"{client_name}_Macro_Calculator.xlsx"
        )

        workbook.save(
            output_file
        )

        return output_file

    except Exception as error:

        logger.exception(
            "Excel calculator error: %s",
            error
        )

        return None


# ============================================================
# GENERATE WORKOUT DOCUMENT
# ============================================================

def generate_workout_docx(
    client_data
):

    template = DocxTemplate(
        str(WORKOUT_TEMPLATE)
    )

    context = {

        "name": client_data["name"],

        "age": client_data["age"],

        "gender": client_data["gender"],

        "height": client_data["height"],

        "weight": client_data["weight"],

        "goal": client_data["goal"],

        "experience": client_data["experience"],

        "equipment": client_data["equipment"],

        "obstacle": client_data["obstacle"],

        "injuries": client_data["injuries"],

        "training_preference":
            client_data[
                "training_preference"
            ],
    }

    template.render(
        context
    )

    client_name = safe_filename(
        client_data["name"]
    )

    output_file = (
        OUTPUT_DIR
        / f"{client_name}_Workout_Blueprint.docx"
    )

    template.save(
        str(output_file)
    )

    return output_file


# ============================================================
# GENERATE NUTRITION DOCUMENT
# ============================================================

def generate_nutrition_docx(
    client_data,
    macros
):

    template = DocxTemplate(
        str(NUTRITION_TEMPLATE)
    )

    context = {

        # CLIENT DATA
        "name": client_data["name"],

        "age": client_data["age"],

        "gender": client_data["gender"],

        "height": client_data["height"],

        "weight": client_data["weight"],

        "goal": client_data["goal"],

        "activity_level":
            client_data[
                "activity_level"
            ],

        "fitness_level":
            client_data[
                "fitness_level"
            ],

        "obstacle":
            client_data[
                "obstacle"
            ],

        "restrictions":
            client_data[
                "restrictions"
            ],

        "injuries":
            client_data[
                "injuries"
            ],

        "meals_per_day":
            client_data[
                "meals_per_day"
            ],

        # MACROS
        "calories":
            macros["calories"],

        "protein":
            macros["protein"],

        "carbs":
            macros["carbs"],

        "fats":
            macros["fats"],

        "water":
            macros["water"],

        "weekly_calories":
            macros[
                "weekly_calories"
            ],

        "bmr":
            macros["bmr"],

        "maintenance_calories":
            macros[
                "maintenance_calories"
            ],

        "activity_multiplier":
            macros[
                "activity_multiplier"
            ],
    }

    template.render(
        context
    )

    client_name = safe_filename(
        client_data["name"]
    )

    output_file = (
        OUTPUT_DIR
        / f"{client_name}_Nutrition_Blueprint.docx"
    )

    template.save(
        str(output_file)
    )

    return output_file


# ============================================================
# START COMMAND
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    welcome_message = """
🏆 SIMON ORIGIN TRANSFORMATION

Welcome!

Send the client's assessment using this exact format:

Name, Age, Gender, Height, Weight, Goal, Experience, Equipment, Obstacle, Activity Level, Fitness Level, Restrictions, Injuries, Meals Per Day, Training Preference

Example:

Abebe Bekele, 28, Male, 175, 82, Fat Loss, Beginner, Gym, Consistency, Moderate, Beginner, None, None, 4, Fat Loss

Height = cm
Weight = kg

The bot will generate:

🏋️ Personalized Workout Blueprint
🥗 Personalized Nutrition Blueprint
🔥 Calories
🥩 Protein
🍚 Carbs
🥑 Fats
💧 Water
"""

    await update.message.reply_text(
        welcome_message
    )


# ============================================================
# HANDLE CLIENT ASSESSMENT
# ============================================================

async def handle_assessment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:

        return

    text = update.message.text.strip()

    try:

        # ----------------------------------------------------
        # SPLIT CLIENT DATA
        # ----------------------------------------------------

        parts = [
            part.strip()
            for part in text.split(",")
        ]

        # We require 15 fields
        if len(parts) != 15:

            await update.message.reply_text(
                f"""
❌ Assessment format error.

I received {len(parts)} fields.

I need exactly 15 fields:

Name, Age, Gender, Height, Weight, Goal, Experience, Equipment, Obstacle, Activity Level, Fitness Level, Restrictions, Injuries, Meals Per Day, Training Preference
"""
            )

            return

        # ----------------------------------------------------
        # CREATE CLIENT DATA
        # ----------------------------------------------------

        client_data = {

            "name": parts[0],

            "age": parts[1],

            "gender": parts[2],

            "height": parts[3],

            "weight": parts[4],

            "goal": parts[5],

            "experience": parts[6],

            "equipment": parts[7],

            "obstacle": parts[8],

            "activity_level": parts[9],

            "fitness_level": parts[10],

            "restrictions": parts[11],

            "injuries": parts[12],

            "meals_per_day": parts[13],

            "training_preference": parts[14],
        }

        # ----------------------------------------------------
        # VALIDATE NUMBERS
        # ----------------------------------------------------

        parse_number(
            client_data["age"],
            "Age"
        )

        parse_number(
            client_data["height"],
            "Height"
        )

        parse_number(
            client_data["weight"],
            "Weight"
        )

        # ----------------------------------------------------
        # PROCESSING MESSAGE
        # ----------------------------------------------------

        processing = await update.message.reply_text(
            f"""
⏳ PROCESSING ASSESSMENT

Client:
{client_data["name"]}

Calculating nutrition...
Creating workout blueprint...
Creating nutrition blueprint...
"""
        )

        # ----------------------------------------------------
        # CALCULATE MACROS
        # ----------------------------------------------------

        macros = calculate_macros(
            client_data
        )

        logger.info(
            "Calculated macros for %s: %s",
            client_data["name"],
            macros
        )

        # ----------------------------------------------------
        # GENERATE WORKOUT
        # ----------------------------------------------------

        workout_file = generate_workout_docx(
            client_data
        )

        # ----------------------------------------------------
        # GENERATE NUTRITION
        # ----------------------------------------------------

        nutrition_file = generate_nutrition_docx(
            client_data,
            macros
        )

        # ----------------------------------------------------
        # CREATE EXCEL RECORD
        # ----------------------------------------------------

        calculator_file = update_calculator(
            client_data,
            macros
        )

        # ----------------------------------------------------
        # SEND WORKOUT
        # ----------------------------------------------------

        with open(
            workout_file,
            "rb"
        ) as file:

            await update.message.reply_document(

                document=file,

                filename=workout_file.name,

                caption=(
                    "🏋️
