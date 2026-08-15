# -*- coding: utf-8 -*-
"""
Calorie & macro calculations - Mifflin-St Jeor, matching the method
stated on the SIMON ORIGIN TRANSFORMATION nutrition template.
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.20,
    "lightly active": 1.375,
    "moderate": 1.55,
    "very active": 1.725,
}

GOAL_ADJUSTMENT = {
    "fat loss": -0.20,
    "muscle gain": 0.15,
    "maintenance": 0.0,
}


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def calc_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if _norm(gender).startswith("m") else base - 161


def calc_targets(weight_kg: float, height_cm: float, age: int, gender: str,
                  activity_level: str, primary_goal: str) -> dict:
    bmr = calc_bmr(weight_kg, height_cm, age, gender)

    activity_key = _norm(activity_level)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_key, 1.375)

    tdee = bmr * multiplier

    goal_key = _norm(primary_goal)
    adjustment = GOAL_ADJUSTMENT.get(goal_key, 0.0)
    calories = tdee * (1 + adjustment)

    protein_g = round(weight_kg * 2.0)
    protein_kcal = protein_g * 4

    fat_g = round((calories * 0.25) / 9)
    fat_kcal = fat_g * 9

    carbs_kcal = max(calories - protein_kcal - fat_kcal, 0)
    carbs_g = round(carbs_kcal / 4)

    calories = round(calories / 10) * 10  # clean round number

    fluid_l = round(weight_kg * 0.035, 1)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": int(calories),
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "fluid_l": fluid_l,
        "weekly_calories": int(calories) * 7,
        "activity_multiplier": multiplier,
        "goal_adjustment_pct": int(adjustment * 100),
    }
