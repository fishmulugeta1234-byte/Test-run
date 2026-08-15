# -*- coding: utf-8 -*-
"""
Ethiopian-forward food database for the meal builder.
Macros are approximate, per 100g of the food AS EATEN/COOKED,
sourced from typical Ethiopian nutrition reference values.
name_am = Amharic label shown alongside the English name.

`contains` lists what a food is NOT free of, e.g. "meat", "dairy", "egg",
"fish", "gluten", "nuts". The meal builder uses this + the client's
diet_restrictions text to decide what's allowed - see _parse_restrictions()
and _restriction_ok() in meal_builder.py.
"""

FOODS = {
    # ---- Staples / carbs ----
    "injera":         {"name_am": "እንጀራ",   "kcal": 168, "protein": 5.5, "carbs": 34, "fat": 1.0, "contains": []},
    "genfo":          {"name_am": "ገንፎ",     "kcal": 140, "protein": 3.5, "carbs": 29, "fat": 1.0, "contains": []},
    "brown_rice":     {"name_am": "ቡናማ ሩዝ",  "kcal": 123, "protein": 2.7, "carbs": 26, "fat": 1.0, "contains": []},
    "white_rice":     {"name_am": "ነጭ ሩዝ",   "kcal": 130, "protein": 2.4, "carbs": 28, "fat": 0.3, "contains": []},
    "oats":           {"name_am": "አጃ",      "kcal": 389, "protein": 16.9, "carbs": 66, "fat": 6.9, "contains": []},
    "boiled_potato":  {"name_am": "ድንች",     "kcal": 87, "protein": 1.9, "carbs": 20, "fat": 0.1, "contains": []},
    "kolo":           {"name_am": "ቆሎ",      "kcal": 360, "protein": 12, "carbs": 65, "fat": 5, "contains": []},
    "bread_dabo":     {"name_am": "ዳቦ",      "kcal": 265, "protein": 9, "carbs": 49, "fat": 3.2, "contains": ["gluten"]},
    "pasta":          {"name_am": "ፓስታ",     "kcal": 158, "protein": 5.8, "carbs": 31, "fat": 0.9, "contains": ["gluten"]},
    "quinoa":         {"name_am": "ኪኖዋ",     "kcal": 120, "protein": 4.4, "carbs": 21, "fat": 1.9, "contains": []},
    "sweet_potato":   {"name_am": "ቆቅ ድንች",  "kcal": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "contains": []},

    # ---- Protein - meat/animal ----
    "doro_tibs":      {"name_am": "የዶሮ ጥብስ",  "kcal": 190, "protein": 27, "carbs": 2, "fat": 8, "contains": ["meat"]},
    "beef_tibs":      {"name_am": "የበሬ ጥብስ",  "kcal": 210, "protein": 26, "carbs": 1, "fat": 11, "contains": ["meat"]},
    "grilled_chicken_breast": {"name_am": "የተጠበሰ ዶሮ ደረት", "kcal": 165, "protein": 31, "carbs": 0, "fat": 3.6, "contains": ["meat"]},
    "minced_beef":    {"name_am": "የተከተፈ ስጋ",  "kcal": 215, "protein": 26, "carbs": 0, "fat": 12, "contains": ["meat"]},
    "lamb_stew":      {"name_am": "የበግ ወጥ",   "kcal": 230, "protein": 25, "carbs": 3, "fat": 13, "contains": ["meat"]},
    "boiled_egg":     {"name_am": "የተቀቀለ እንቁላል", "kcal": 155, "protein": 13, "carbs": 1.1, "fat": 11, "contains": ["egg"]},
    "scrambled_egg":  {"name_am": "የደበለቀ እንቁላል", "kcal": 148, "protein": 10, "carbs": 1.6, "fat": 11, "contains": ["egg", "dairy"]},
    "ergo":           {"name_am": "እርጎ",      "kcal": 61, "protein": 3.5, "carbs": 4.7, "fat": 3.3, "contains": ["dairy"]},
    "cheese_ayib":    {"name_am": "አይብ",      "kcal": 174, "protein": 20, "carbs": 3, "fat": 9, "contains": ["dairy"]},
    "milk":           {"name_am": "ወተት",      "kcal": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "contains": ["dairy"]},
    "fish_asa":       {"name_am": "አሳ",       "kcal": 140, "protein": 24, "carbs": 0, "fat": 4.5, "contains": ["fish"]},
    "tuna_canned":    {"name_am": "ቱና",       "kcal": 116, "protein": 26, "carbs": 0, "fat": 1, "contains": ["fish"]},
    "turkey_breast":  {"name_am": "ተርኪ",      "kcal": 135, "protein": 30, "carbs": 0, "fat": 1, "contains": ["meat"]},

    # ---- Protein - plant / legumes ----
    "misir_wot":      {"name_am": "ምስር ወጥ",   "kcal": 130, "protein": 8, "carbs": 18, "fat": 3.5, "contains": []},
    "shiro_wot":      {"name_am": "ሽሮ ወጥ",    "kcal": 145, "protein": 7, "carbs": 16, "fat": 6, "contains": []},
    "kik_alicha":     {"name_am": "ክክ አልጫ",   "kcal": 118, "protein": 7.5, "carbs": 19, "fat": 1.5, "contains": []},
    "chickpeas":      {"name_am": "ሽምብራ",     "kcal": 164, "protein": 8.9, "carbs": 27, "fat": 2.6, "contains": []},
    "ful_medames":    {"name_am": "ፉል",       "kcal": 110, "protein": 7.6, "carbs": 17, "fat": 1.3, "contains": []},
    "lentil_soup":    {"name_am": "የምስር ሾርባ",  "kcal": 116, "protein": 9, "carbs": 20, "fat": 0.4, "contains": []},
    "tofu":           {"name_am": "ቶፉ",       "kcal": 76, "protein": 8, "carbs": 1.9, "fat": 4.8, "contains": []},
    "tempeh":         {"name_am": "ቴምፔ",      "kcal": 193, "protein": 19, "carbs": 9, "fat": 11, "contains": []},

    # ---- Vegetables ----
    "gomen":          {"name_am": "ጎመን",      "kcal": 32, "protein": 2.6, "carbs": 5, "fat": 0.4, "contains": []},
    "salata":         {"name_am": "ሰላጣ",      "kcal": 20, "protein": 1.2, "carbs": 4, "fat": 0.2, "contains": []},
    "atkilt":         {"name_am": "አትክልት",    "kcal": 45, "protein": 1.8, "carbs": 8, "fat": 1.2, "contains": []},
    "tikil_gomen":    {"name_am": "ጥቅል ጎመን",   "kcal": 38, "protein": 1.6, "carbs": 6, "fat": 1.0, "contains": []},
    "spinach":        {"name_am": "ስፒናች",     "kcal": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "contains": []},
    "broccoli":       {"name_am": "ብሮኮሊ",     "kcal": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "contains": []},

    # ---- Fats / nuts / extras ----
    "avocado":        {"name_am": "አቮካዶ",     "kcal": 160, "protein": 2, "carbs": 8.5, "fat": 14.7, "contains": []},
    "peanuts":        {"name_am": "ኦቾሎኒ",     "kcal": 567, "protein": 25.8, "carbs": 16, "fat": 49, "contains": ["nuts"]},
    "almonds":        {"name_am": "ለውዝ",      "kcal": 579, "protein": 21, "carbs": 22, "fat": 50, "contains": ["nuts"]},
    "niter_kibbeh":   {"name_am": "የተለወጠ ቅቤ",  "kcal": 717, "protein": 0.9, "carbs": 0.1, "fat": 81, "contains": ["dairy"]},
    "olive_oil":      {"name_am": "የወይራ ዘይት",  "kcal": 884, "protein": 0, "carbs": 0, "fat": 100, "contains": []},

    # ---- Fruit / snack ----
    "banana":         {"name_am": "ሙዝ",       "kcal": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "contains": []},
    "mango":          {"name_am": "ማንጎ",      "kcal": 60, "protein": 0.8, "carbs": 15, "fat": 0.4, "contains": []},
    "papaya":         {"name_am": "ፓፓያ",      "kcal": 43, "protein": 0.5, "carbs": 11, "fat": 0.3, "contains": []},
    "orange":         {"name_am": "ብርቱካን",    "kcal": 47, "protein": 0.9, "carbs": 12, "fat": 0.1, "contains": []},
    "dates":          {"name_am": "ተምር",      "kcal": 282, "protein": 2.5, "carbs": 75, "fat": 0.4, "contains": []},
}

# Meal templates: each is a list of (food_key, base_grams) pairs at a
# reference ~500 kcal serving. The meal builder scales grams up/down to
# hit each client's per-meal calorie target while holding ratios constant.
# Extra combos = more variety so plans don't feel repetitive across weeks,
# and more room to route around a client's disliked foods.
MEAL_TEMPLATES = {
    "breakfast": [
        [("genfo", 250), ("peanuts", 15), ("banana", 100)],
        [("injera", 120), ("ful_medames", 200), ("olive_oil", 5)],
        [("oats", 60), ("ergo", 150), ("banana", 100)],
        [("bread_dabo", 90), ("boiled_egg", 100), ("avocado", 50)],
        [("oats", 55), ("milk", 200), ("dates", 40)],
        [("scrambled_egg", 120), ("bread_dabo", 70), ("avocado", 40)],
        [("kolo", 70), ("ergo", 100), ("mango", 80)],
        [("sweet_potato", 200), ("boiled_egg", 100), ("spinach", 60)],
    ],
    "lunch": [
        [("injera", 180), ("misir_wot", 220), ("gomen", 100)],
        [("brown_rice", 150), ("grilled_chicken_breast", 150), ("salata", 100)],
        [("injera", 180), ("shiro_wot", 220), ("salata", 80)],
        [("boiled_potato", 200), ("beef_tibs", 150), ("gomen", 100)],
        [("white_rice", 150), ("fish_asa", 150), ("broccoli", 100)],
        [("pasta", 130), ("minced_beef", 120), ("tikil_gomen", 100)],
        [("quinoa", 130), ("chickpeas", 150), ("atkilt", 100)],
        [("injera", 170), ("lamb_stew", 150), ("salata", 80)],
        [("brown_rice", 140), ("tofu", 180), ("broccoli", 100)],
    ],
    "dinner": [
        [("injera", 150), ("doro_tibs", 180), ("gomen", 100)],
        [("brown_rice", 130), ("fish_asa", 150), ("salata", 100)],
        [("injera", 150), ("kik_alicha", 200), ("salata", 80)],
        [("boiled_potato", 180), ("grilled_chicken_breast", 150), ("gomen", 100)],
        [("sweet_potato", 180), ("turkey_breast", 150), ("spinach", 100)],
        [("quinoa", 120), ("lentil_soup", 200), ("atkilt", 90)],
        [("pasta", 120), ("tuna_canned", 130), ("tikil_gomen", 90)],
        [("injera", 150), ("tempeh", 150), ("gomen", 90)],
    ],
    "snack": [
        [("kolo", 60), ("banana", 100)],
        [("ergo", 150), ("mango", 100)],
        [("peanuts", 30), ("mango", 100)],
        [("boiled_egg", 100), ("salata", 50)],
        [("almonds", 25), ("orange", 100)],
        [("cheese_ayib", 60), ("papaya", 100)],
        [("dates", 30), ("almonds", 15)],
        [("tofu", 80), ("orange", 80)],
    ],
}

# Recognized diet-restriction keywords -> which "contains" tags to exclude.
# vegan and vegetarian are intentionally different (vegetarian still allows
# dairy/egg). Multiple restrictions can combine (e.g. "vegetarian, gluten-free").
DIET_EXCLUDES = {
    "vegan": {"meat", "fish", "dairy", "egg"},
    "vegetarian": {"meat", "fish"},
    "pescatarian": {"meat"},
    "dairy free": {"dairy"},
    "dairy-free": {"dairy"},
    "lactose": {"dairy"},
    "nut free": {"nuts"},
    "nut-free": {"nuts"},
    "gluten": {"gluten"},
}
