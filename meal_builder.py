# -*- coding: utf-8 -*-
"""
Builds a 7-day, 4-meal Ethiopian-forward meal matrix scaled to hit each
client's calorie/protein targets. Uses fixed-ratio meal templates from
data/foods.py and scales grams per meal to match target calories.
"""
from data.foods import FOODS, MEAL_TEMPLATES, DIET_EXCLUDES

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS_AM = ["ሰኞ", "ማክሰኞ", "ረቡዕ", "ሐሙስ", "አርብ", "ቅዳሜ", "እሁድ"]

# Meal calorie split across the day (breakfast/lunch/dinner/snack)
MEAL_SPLIT = {"breakfast": 0.27, "lunch": 0.33, "dinner": 0.30, "snack": 0.10}

# Distinct fixed offsets per meal slot so each slot's rotation is out of phase
# with the others, even when a restricted pool shrinks to just 1-3 items
# (a plain multiplier like i*3 gets nullified by modulo on small pools - avoid that).
_MEAL_OFFSET = {"breakfast": 0, "lunch": 2, "dinner": 5, "snack": 7}


def _template_kcal(template) -> float:
    total = 0.0
    for food_key, grams in template:
        f = FOODS[food_key]
        total += f["kcal"] * grams / 100
    return total


def _restriction_ok(template, excluded_tags: set, dislike_terms: list) -> bool:
    for food_key, _ in template:
        food = FOODS[food_key]
        if excluded_tags & set(food["contains"]):
            return False
        label = food_key.replace("_", " ")
        for term in dislike_terms:
            if term and (term in label or term in food["name_am"]):
                return False
    return True


def _parse_restrictions(text: str) -> set:
    t = (text or "").lower()
    excluded = set()
    for keyword, tags in DIET_EXCLUDES.items():
        if keyword in t:
            excluded |= tags
    return excluded


def _parse_dislikes(text: str) -> list:
    return [t.strip().lower() for t in (text or "").split(",") if t.strip()]


def _scale_meal(template, target_kcal):
    base_kcal = _template_kcal(template)
    scale = target_kcal / base_kcal if base_kcal else 1.0
    items = []
    kcal_sum = protein_sum = 0.0
    for food_key, grams in template:
        g = round(grams * scale)
        f = FOODS[food_key]
        kcal_sum += f["kcal"] * g / 100
        protein_sum += f["protein"] * g / 100
        label_en = food_key.replace("_", " ").title()
        items.append(f"{label_en} ({f['name_am']}) - {g}g")
    return items, round(kcal_sum), round(protein_sum)


def build_meal_plan(assessment: dict, targets: dict) -> dict:
    """
    assessment keys used: diet_restrictions, full_name (for deterministic seed)
    targets: output of calculations.calc_targets
    Returns {"rows": [ {day_en, day_am, meals:[m1,m2,m3,m4], kcal, protein} ... ]}
    """
    restriction_tags = _parse_restrictions(assessment.get("diet_restrictions", ""))
    dislike_terms = _parse_dislikes(assessment.get("food_dislikes", ""))

    daily_kcal = targets["calories"]
    rows = []
    for i, (day_en, day_am) in enumerate(zip(DAYS, DAYS_AM)):
        meals_out = []
        day_kcal_total = 0
        day_protein_total = 0
        for meal_key in ["breakfast", "lunch", "dinner", "snack"]:
            pool = [t for t in MEAL_TEMPLATES[meal_key] if _restriction_ok(t, restriction_tags, dislike_terms)]
            if not pool:
                # dislikes are a preference, not a hard rule - relax those first
                pool = [t for t in MEAL_TEMPLATES[meal_key] if _restriction_ok(t, restriction_tags, [])]
            if not pool:
                pool = MEAL_TEMPLATES[meal_key]
            # Deterministic per-client, per-meal-slot rotation through the pool.
            template = pool[(i + _MEAL_OFFSET[meal_key]) % len(pool)]
            target_kcal = daily_kcal * MEAL_SPLIT[meal_key]
            items, kcal, protein = _scale_meal(template, target_kcal)
            meals_out.append({"items": items, "kcal": kcal, "protein": protein})
            day_kcal_total += kcal
            day_protein_total += protein
        rows.append({
            "day_en": day_en, "day_am": day_am,
            "meals": meals_out,
            "kcal": day_kcal_total, "protein": day_protein_total,
        })
    return {"rows": rows}
