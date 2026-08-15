# -*- coding: utf-8 -*-
"""
Main entry point. Plug this into your Telegram/WhatsApp bot: call
generate_blueprints(assessment_dict) whenever a new client assessment
comes in, and send the two returned PDF paths back to the client.
"""
import os
import re
import datetime

from generate_workout_pdf import generate_workout_pdf
from generate_nutrition_pdf import generate_nutrition_pdf

REQUIRED_FIELDS = ["full_name", "gender", "age", "height_cm", "weight_kg", "primary_goal"]


def _safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\- ]", "", name).strip().replace(" ", "_")
    return name or "client"


def validate_assessment(assessment: dict):
    missing = [f for f in REQUIRED_FIELDS if not assessment.get(f)]
    if missing:
        raise ValueError(f"Assessment is missing required field(s): {', '.join(missing)}")


def generate_blueprints(assessment: dict, out_dir: str = "outputs") -> dict:
    """
    assessment: dict collected from your intake form/bot, e.g.:
        {
            "full_name": "Bethlehem Tesfaye",
            "gender": "Female",                # "male" / "female"
            "age": 27,
            "height_cm": 165,
            "weight_kg": 68,
            "primary_goal": "Fat Loss",         # "Fat Loss" / "Muscle Gain" / "Maintenance"
            "activity_level": "Moderate",       # Sedentary / Lightly Active / Moderate / Very Active
            "training_experience": "Beginner",  # Beginner / Intermediate / Advanced
            "equipment_available": "Home",      # Home / Gym / Both
            "main_obstacle": "Consistency",
            "diet_restrictions": "None",        # e.g. "Vegan", "Vegetarian", "Gluten-free", "Dairy-free", "Nut-free" (combinable: "Vegetarian, gluten-free")
            "food_dislikes": "None",            # free text, comma-separated, e.g. "mango, chickpeas"
            "health_injuries": "None",
            "exercise_dislikes": "None",        # free text, comma-separated, e.g. "burpee, lunges"
            "training_preference": "Fat Loss",
            "date": "2026-08-15",               # optional, defaults to today
        }
    Returns {"workout_pdf": path, "nutrition_pdf": path}
    """
    validate_assessment(assessment)
    assessment = dict(assessment)
    assessment.setdefault("date", datetime.date.today().isoformat())

    os.makedirs(out_dir, exist_ok=True)
    fname = _safe_filename(assessment["full_name"])

    workout_path = os.path.join(out_dir, f"{fname}_Workout_Blueprint.pdf")
    nutrition_path = os.path.join(out_dir, f"{fname}_Nutrition_Blueprint.pdf")

    generate_workout_pdf(assessment, workout_path)
    generate_nutrition_pdf(assessment, nutrition_path)

    return {"workout_pdf": workout_path, "nutrition_pdf": nutrition_path}


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate.py assessment.json [out_dir]")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        assessment = json.load(f)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
    result = generate_blueprints(assessment, out_dir)
    print(json.dumps(result, indent=2))
