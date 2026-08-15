# Simon Origin Transformation — Blueprint Generator

Generates personalized, bilingual (English / Amharic) **30-Day Workout** and
**30-Day Nutrition** PDF blueprints from a single client assessment. Built for
an Ethiopian fitness coaching audience — calorie/macro math is real
(Mifflin-St Jeor), workout exercises are filtered for equipment/injuries, and
the meal plan is built from Ethiopian staples (injera, shiro, misir wot,
doro tibs, ergo, kolo, teff dishes, etc.).

Drop this into any bot (Telegram, WhatsApp, a web form) — feed it the intake
data, get two PDFs back.

## Quick start

```bash
pip install -r requirements.txt
python generate.py example_assessment.json outputs
```

This writes two files into `outputs/`:
- `<Client_Name>_Workout_Blueprint.pdf`
- `<Client_Name>_Nutrition_Blueprint.pdf`

## Using it from your bot

```python
from generate import generate_blueprints

assessment = {
    "full_name": "Bethlehem Tesfaye",
    "gender": "Female",                 # "male" / "female"
    "age": 27,
    "height_cm": 165,
    "weight_kg": 68,
    "primary_goal": "Fat Loss",         # "Fat Loss" / "Muscle Gain" / "Maintenance"
    "activity_level": "Moderate",       # Sedentary / Lightly Active / Moderate / Very Active
    "training_experience": "Beginner",  # Beginner / Intermediate / Advanced
    "equipment_available": "Home",      # Home / Gym / Both
    "main_obstacle": "Consistency",
    "diet_restrictions": "None",        # e.g. "Vegan", "Vegetarian", "Gluten-free", "Dairy-free", "Nut-free" (combinable)
    "food_dislikes": "None",            # free text, comma-separated, e.g. "mango, chickpeas"
    "health_injuries": "None",          # free text, e.g. "knee", "lower back"
    "exercise_dislikes": "None",        # free text, comma-separated, e.g. "burpee, lunges"
    "training_preference": "Fat Loss",
}

result = generate_blueprints(assessment, out_dir="outputs")
# {"workout_pdf": "outputs/Bethlehem_Tesfaye_Workout_Blueprint.pdf",
#  "nutrition_pdf": "outputs/Bethlehem_Tesfaye_Nutrition_Blueprint.pdf"}
```

Send `result["workout_pdf"]` and `result["nutrition_pdf"]` back to the client
however your bot delivers files (Telegram `send_document`, email attachment,
a download link, etc).

Only `full_name`, `gender`, `age`, `height_cm`, `weight_kg`, and
`primary_goal` are required — everything else has a sensible default.

## How it works

| Module | Responsibility |
|---|---|
| `calculations.py` | BMR (Mifflin-St Jeor) → TDEE → goal-adjusted calories → protein/carb/fat/fluid targets |
| `workout_builder.py` | Builds the 7-day split, filtering exercises by equipment and **excluding anything that conflicts with reported injuries** (injury safety is never relaxed — experience level is relaxed first if a day's pool is too small) |
| `meal_builder.py` | Builds a 7-day, 4-meal Ethiopian meal matrix, scaling portions (grams) to hit the day's calorie/protein targets; respects vegan/gluten-free restrictions |
| `data/exercises.py` | Exercise library, tagged by movement pattern / equipment / injury flag / level |
| `data/foods.py` | Ethiopian food database (kcal/protein/carbs/fat per 100g) + meal templates |
| `pdf_render.py` | Shared branding (header, snapshot table, section styles) and the Amharic/Latin mixed-font rendering fix (see below) |
| `generate_workout_pdf.py` / `generate_nutrition_pdf.py` | Assemble each document |
| `generate.py` | Main entry point — call `generate_blueprints(assessment)` from your bot |

### The Amharic font gotcha

`Noto Sans Ethiopic` (bundled in `fonts/`) only contains Ethiopic-script
glyphs — no Latin letters or ASCII digits. Any string that mixes English or
numbers with Amharic (which is most of this document — dates, kcal counts,
gram amounts) will render as black "tofu" boxes if you set one font for the
whole paragraph. `pdf_render.mixed_font()` scans each string, wraps only the
Ethiopic-script runs in the Noto font, and leaves the rest in the base
Helvetica style. Use it any time you build a paragraph that mixes scripts.

## Customizing

- **Exercises** (84 in the library): add/edit entries in `data/exercises.py`.
  Each has `equipment` (`bodyweight`/`home`/`gym`/`both` — `bodyweight` needs
  no equipment and is always available), `injury_flags` (body-area keywords
  to hard-exclude on), and `level` (`beginner`/`intermediate`/`advanced`).
- **Foods & meals** (48 foods, 33 meal combos): add/edit `data/foods.py`.
  `FOODS` holds macros per 100g plus a `contains` list (`meat`, `fish`,
  `dairy`, `egg`, `gluten`, `nuts`); `MEAL_TEMPLATES` holds base combos per
  meal slot scaled to the client's targets; `DIET_EXCLUDES` maps restriction
  keywords (vegan, vegetarian, dairy-free, nut-free, gluten...) to which
  `contains` tags get excluded.
- **Per-client preferences without touching code**: the assessment dict
  accepts `diet_restrictions` (diet type, can combine e.g.
  "Vegetarian, gluten-free"), `food_dislikes` (comma-separated foods to
  avoid), `health_injuries` (comma-separated body areas — never relaxed),
  and `exercise_dislikes` (comma-separated exercises to avoid). Injury
  exclusions are a hard safety rule; dislikes are a soft preference that
  only relaxes if honoring it would leave a day/meal empty.
- **Branding**: colors/fonts/layout live in `pdf_render.py`
  (`INK`, `GOLD`, `LIGHT_GOLD` at the top).
- **Coach handle / brand name**: passed as parameters to `build_header()` /
  `footer_note()` in the generator files — change the default there.

## Notes on the numbers

Calorie/macro targets and meal portions are estimates from standard formulas
and typical food composition data — treat this as a coaching starting point,
not medical advice. Always have clients confirm allergies/restrictions and
adjust for how they respond.

## License

Noto Sans Ethiopic is licensed under the SIL Open Font License 1.1
(bundled in `fonts/`, sourced from the
[Noto Fonts project](https://github.com/googlefonts/noto-fonts)).
Everything else in this repo is yours to use for your business.
