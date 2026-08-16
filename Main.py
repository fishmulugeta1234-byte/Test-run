import os
import re
import logging
import asyncio
from pathlib import Path
from datetime import datetime

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

WORKOUT_TEMPLATE = BASE_DIR / "Simon_30Day_Workout_Blueprint_Updated.docx"
NUTRITION_TEMPLATE = BASE_DIR / "Simon_30Day_Nutrition_Blueprint.docx"
CALCULATOR_FILE = BASE_DIR / "Simon_Calorie_Macro_Calculator.xlsx"

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is not set. "
        "Add it to your Render Environment Variables."
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
# TEMPLATE CHECK
# ============================================================

def check_required_files():
    missing = []

    required_files = [
        WORKOUT_TEMPLATE,
        NUTRITION_TEMPLATE,
        CALCULATOR_FILE,
    ]

    for file in required_files:
        if not file.exists():
            missing.append(str(file.name))

    if missing:
        raise FileNotFoundError(
            "Missing required files:\n" + "\n".join(missing)
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_filename(name):
    """
    Converts client name into a safe filename.
    """

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

    return name or "Client"


def clean_value(value, default=""):
    if value is None:
        return default

    return str(value).strip()


def parse_number(value, field_name):
    """
    Convert text to float and provide a useful error.
    """

    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        raise ValueError(
            f"{field_name} must be a number."
        )


# ============================================================
# MACRO CALCULATION
# ============================================================

def calculate_macros(client_data):
    """
    Calculates calories and macros.

    The nutrition template states that targets are based on:
    Mifflin-St Jeor BMR x activity multiplier,
    followed by a goal adjustment.

    This function implements that method.
    """

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

    activity = client_data["activity_level"].lower().strip()

    goal = client_data["goal"].lower().strip()

    # --------------------------------------------------------
    # Mifflin-St Jeor
    # --------------------------------------------------------

    if gender in ["male", "m", "man"]:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5

    elif gender in ["female", "f", "woman"]:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    else:
        # Neutral fallback if gender wasn't recognized.
        bmr = (10 * weight) + (6.25 * height) - (5 * age)

    # --------------------------------------------------------
    # Activity multiplier
    # --------------------------------------------------------

    activity_multipliers = {
        "sedentary": 1.20,
        "lightly active": 1.375,
        "light": 1.375,
        "moderate": 1.55,
        "moderately active": 1.55,
        "very active": 1.725,
        "extremely active": 1.90,
    }

    activity_multiplier = activity_multipliers.get(
        activity,
        1.55
    )

    maintenance_calories = bmr * activity_multiplier

    # --------------------------------------------------------
    # Goal adjustment
    # --------------------------------------------------------

    if "fat" in goal and "loss" in goal:
        calories = maintenance_calories * 0.85

    elif "lose" in goal or "weight loss" in goal:
        calories = maintenance_calories * 0.85

    elif "muscle" in goal and "gain" in goal:
        calories = maintenance_calories * 1.10

    elif "gain" in goal:
        calories = maintenance_calories * 1.10

    else:
        calories = maintenance_calories

    calories = round(calories)

    # --------------------------------------------------------
    # Protein
    # --------------------------------------------------------

    protein = round(weight * 2.0)

    # --------------------------------------------------------
    # Fat
    # --------------------------------------------------------

    fats = round(weight * 0.9)

    # --------------------------------------------------------
    # Carbohydrates
    # --------------------------------------------------------

    calories_from_protein = protein * 4
    calories_from_fat = fats * 9

    remaining_calories = (
        calories
        - calories_from_protein
        - calories_from_fat
    )

    carbs = round(
        max(remaining_calories, 0) / 4
    )

    # --------------------------------------------------------
    # Water
    # --------------------------------------------------------

    water = round(weight * 0.035, 1)

    # --------------------------------------------------------
    # Weekly calories
    # --------------------------------------------------------

    weekly_calories = calories * 7

    return {
        "calories": calories,
        "protein": protein,
        "fats": fats,
        "carbs": carbs,
        "water": water,
        "weekly_calories": weekly_calories,

        # Additional values available to the template
        "bmr": round(bmr),
        "maintenance_calories": round(maintenance_calories),
        "activity_multiplier": activity_multiplier,
    }


# ============================================================
# OPTIONAL EXCEL INTEGRATION
# ============================================================

def update_calculator_copy(client_data, macros):
    """
    Updates the Bot Calculator sheet with the client's data.

    This does NOT control the calculations used by the bot.
    The Python calculation above is the source of truth.

    The spreadsheet is maintained as a record/calculator copy.
    """

    try:

        wb = load_workbook(
            CALCULATOR_FILE
        )

        if "Bot Calculator" not in wb.sheetnames:
            ws = wb.create_sheet(
                "Bot Calculator",
                0
            )
        else:
            ws = wb["Bot Calculator"]

        ws["B3"] = float(client_data["weight"])
        ws["B4"] = float(
            macros["activity_multiplier"]
        )

        ws["B5"] = macros["calories"]
        ws["B6"] = macros["protein"]
        ws["B7"] = macros["fats"]
        ws["B8"] = macros["carbs"]

        # Do not overwrite the original calculator.
        client_name = safe_filename(
            client_data["name"]
        )

        output_file = (
            OUTPUT_DIR /
            f"{client_name}_Macro_Calculator.xlsx"
        )

        wb.save(output_file)

        return output_file

    except Exception as e:

        logger.exception(
            "Could not update calculator copy."
        )

        return None


# ============================================================
# WORKOUT DOCUMENT
# ============================================================

def generate_workout_docx(client_data):
    """
    Generates personalized workout document.
    """

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
        "training_preference": client_data[
            "training_preference"
        ],
    }

    template.render(context)

    client_name = safe_filename(
        client_data["name"]
    )

    output_file = (
        OUTPUT_DIR /
        f"{client_name}_Workout_Blueprint.docx"
    )

    template.save(
        str(output_file)
    )

    return output_file


# ============================================================
# NUTRITION DOCUMENT
# ============================================================

def generate_nutrition_docx(
    client_data,
    macros
):
    """
    Generates personalized nutrition document.
    """

    template = DocxTemplate(
        str(NUTRITION_TEMPLATE)
    )

    context = {
        # Client information
        "name": client_data["name"],
        "age": client_data["age"],
        "gender": client_data["gender"],
        "height": client_data["height"],
        "weight": client_data["weight"],
        "goal": client_data["goal"],
        "activity_level": client_data[
            "activity_level"
        ],
        "fitness_level": client_data[
            "fitness_level"
        ],
        "obstacle": client_data["obstacle"],
        "restrictions": client_data[
            "restrictions"
        ],
        "injuries": client_data[
            "injuries"
        ],
        "meals_per_day": client_data[
            "meals_per_day"
        ],

        # Nutrition calculations
        "calories": macros["calories"],
        "protein": macros["protein"],
        "carbs": macros["carbs"],
        "fats": macros["fats"],
        "water": macros["water"],
        "weekly_calories": macros[
            "weekly_calories"
        ],

        # Extra values
        "bmr": macros["bmr"],
        "maintenance_calories": macros[
            "maintenance_calories"
        ],
        "activity_multiplier": macros[
            "activity_multiplier"
        ],
    }

    template.render(context)

    client_name = safe_filename(
        client_data["name"]
    )

    output_file = (
        OUTPUT_DIR /
        f"{client_name}_Nutrition_Blueprint.docx"
    )

    template.save(
        str(output_file)
    )

    return output_file


# ============================================================
# TELEGRAM /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = """
🏆 SIMON ORIGIN TRANSFORMATION

Welcome!

Send the client's assessment using this format:

Name, Age, Gender, Height, Weight, Goal, Experience, Equipment, Obstacle, Activity Level, Fitness Level, Restrictions, Injuries, Meals Per Day, Training Preference

Example:

Abebe Bekele, 28, Male, 175, 82, Fat Loss, Beginner, Gym, Consistency, Moderate, Beginner, None, None, 4, Fat Loss

📌 Height = cm
📌 Weight = kg

The bot will automatically generate:

📄 Personalized Workout Blueprint
📄 Personalized Nutrition Blueprint
📊 Calorie & Macro Calculation
"""

    await update.message.reply_text(
        message
    )


# ============================================================
# ASSESSMENT HANDLER
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
        # Split assessment
        # ----------------------------------------------------

        parts = [
            p.strip()
            for p in text.split(",")
        ]

        if len(parts) != 15:

            await update.message.reply_text(
                f"""
❌ I couldn't process the assessment.

I received {len(parts)} fields, but I need exactly 15.

Please use:

Name, Age, Gender, Height, Weight, Goal, Experience, Equipment, Obstacle, Activity Level, Fitness Level, Restrictions, Injuries, Meals Per Day, Training Preference
"""
            )

            return

        # ----------------------------------------------------
        # Client data
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
        # Validate numeric values
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
        # Processing message
        # ----------------------------------------------------

        processing_message = await update.message.reply_text(
            f"""
⏳ Processing assessment for:

{client_data["name"]}

Calculating nutrition targets...
Creating workout blueprint...
Creating nutrition blueprint...
"""
        )

        # ----------------------------------------------------
        # Calculate macros
        # ----------------------------------------------------

        macros = calculate_macros(
            client_data
        )

        logger.info(
            "Macros calculated for %s: %s",
            client_data["name"],
            macros
        )

        # ----------------------------------------------------
        # Generate documents
        # ----------------------------------------------------

        workout_file = generate_workout_docx(
            client_data
        )

        nutrition_file = generate_nutrition_docx(
            client_data,
            macros
        )

        # ----------------------------------------------------
        # Optional Excel record
        # ----------------------------------------------------

        calculator_file = (
            update_calculator_copy(
                client_data,
                macros
            )
        )

        # ----------------------------------------------------
        # Send workout
        # ----------------------------------------------------

        with open(
            workout_file,
            "rb"
        ) as document:

            await update.message.reply_document(
                document=document,
                filename=workout_file.name,
                caption=(
                    "🏋️ Your Personalized "
                    "30-Day Workout Blueprint"
                ),
            )

        # ----------------------------------------------------
        # Send nutrition
        # ----------------------------------------------------

        with open(
            nutrition_file,
            "rb"
        ) as document:

            await update.message.reply_document(
                document=document,
                filename=nutrition_file.name,
                caption=(
                    "🥗 Your Personalized "
                    "30-Day Nutrition Blueprint"
                ),
            )

        # ----------------------------------------------------
        # Send macro summary
        # ----------------------------------------------------

        await update.message.reply_text(
            f"""
✅ BLUEPRINTS COMPLETED

👤 Client: {client_data["name"]}

🔥 Daily Calories:
{macros["calories"]} kcal

🥩 Protein:
{macros["protein"]} g

🍚 Carbohydrates:
{macros["carbs"]} g

🥑 Fat:
{macros["fats"]} g

💧 Water:
{macros["water"]} L

📊 Weekly Calories:
{macros["weekly_calories"]:,} kcal

The personalized workout and nutrition documents have been sent above.
"""
        )

        # ----------------------------------------------------
        # Delete temporary generated files
        # ----------------------------------------------------

        try:

            if workout_file.exists():
                workout_file.unlink()

            if nutrition_file.exists():
                nutrition_file.unlink()

            if calculator_file and calculator_file.exists():
                calculator_file.unlink()

        except Exception:

            logger.exception(
                "Could not clean generated files."
            )

        # ----------------------------------------------------
        # Delete processing message
        # ----------------------------------------------------

        try:

            await processing_message.delete()

        except Exception:

            pass

    except Exception as e:

        logger.exception(
            "Assessment processing failed."
        )

        await update.message.reply_text(
            f"""
❌ ERROR PROCESSING ASSESSMENT

The assessment could not be completed.

Error:
{str(e)}

Please check the assessment format and try again.
"""
        )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.exception(
        "Telegram bot error:",
        exc_info=context.error
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "Checking required files..."
    )

    check_required_files()

    logger.info(
        "All required files found."
    )

    logger.info(
        "Starting Simon Origin Transformation Bot..."
    )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Assessment messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_assessment
        )
    )

    # Error handling
    app.add_error_handler(
        error_handler
    )

    logger.info(
        "Bot is running..."
    )

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":
    main()
