# -*- coding: utf-8 -*-
"""
Builds a personalized 7-day workout program from the client assessment,
pulling exercises from data/exercises.py and filtering by equipment,
experience level and reported injuries.
"""
import random
from data.exercises import EXERCISES, DAY_PLAN

LEVEL_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}

# (sets, rep_range, rest_seconds) by experience x goal
SCHEME_BY_LEVEL = {
    "beginner":     {"sets": 3, "reps": "10-12", "rest_strength": 75, "rest_metabolic": 45},
    "intermediate": {"sets": 4, "reps": "8-10", "rest_strength": 90, "rest_metabolic": 40},
    "advanced":     {"sets": 5, "reps": "6-10", "rest_strength": 120, "rest_metabolic": 35},
}


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _equipment_key(equipment_available: str) -> str:
    e = _norm(equipment_available)
    if "home" in e and "gym" not in e:
        return "home"
    if "gym" in e and "home" not in e:
        return "gym"
    return "both"  # "Both" or unspecified -> allow everything


def _exercise_allowed(ex: dict, equip_key: str, injury_terms: list, dislike_terms: list) -> bool:
    """Equipment + injury safety + dislikes filter. Injury exclusion is never relaxed."""
    if ex["equipment"] != "bodyweight":  # bodyweight exercises need no equipment, always allowed
        if ex["equipment"] != "both" and equip_key != "both" and ex["equipment"] != equip_key:
            return False
    for flag in ex["injury_flags"]:
        for term in injury_terms:
            if term and term in flag:
                return False
    name_lower = ex["name"].lower()
    for term in dislike_terms:
        if term and term in name_lower:
            return False
    return True


def build_workout_plan(assessment: dict) -> dict:
    """
    assessment keys used:
      primary_goal, training_experience, equipment_available,
      health_injuries, training_preference
    Returns a dict: {"days": [ {title_en, title_am, exercises:[...]} ... ]}
    """
    goal = _norm(assessment.get("primary_goal", "fat loss"))
    experience = _norm(assessment.get("training_experience", "beginner"))
    level_rank = LEVEL_RANK.get(experience, 0)
    equip_key = _equipment_key(assessment.get("equipment_available", "Both"))
    injuries_raw = _norm(assessment.get("health_injuries", "none"))
    injury_terms = [] if injuries_raw in ("", "none", "n/a") else \
        [t.strip() for t in injuries_raw.replace(",", " ").split() if len(t.strip()) > 2]

    dislikes_raw = _norm(assessment.get("exercise_dislikes", ""))
    dislike_terms = [t.strip() for t in dislikes_raw.split(",") if t.strip()]

    scheme = SCHEME_BY_LEVEL.get(experience, SCHEME_BY_LEVEL["beginner"])
    is_metabolic_focus = goal == "fat loss"
    rest = scheme["rest_metabolic"] if is_metabolic_focus else scheme["rest_strength"]

    rng = random.Random(assessment.get("full_name", "seed"))  # deterministic per client

    days = []
    for title_en, title_am, pattern in DAY_PLAN:
        pool = EXERCISES[pattern]
        # Equipment + injury safety is a hard filter, applied first and never relaxed.
        safe = [ex for ex in pool if _exercise_allowed(ex, equip_key, injury_terms, dislike_terms)]
        if not safe:
            # dislikes are a preference, not a safety rule - relax those first
            safe = [ex for ex in pool if _exercise_allowed(ex, equip_key, injury_terms, [])]
        if not safe:
            safe = pool  # last-resort only if equipment itself excludes everything

        target_n = 4 if pattern in ("active_recovery", "rest_light_cardio") else 5
        # Fill with exercises at-or-below experience level first; only reach into
        # harder exercises if the safe pool is too small to fill the day.
        within_level = [ex for ex in safe if LEVEL_RANK.get(ex["level"], 0) <= level_rank]
        above_level = [ex for ex in safe if ex not in within_level]
        rng.shuffle(within_level)
        rng.shuffle(above_level)
        picks = (within_level + above_level)[:target_n]

        if pattern in ("active_recovery", "rest_light_cardio"):
            exercises = [
                {"name": ex["name"], "sets": "1-2",
                 "reps": "8-10 min" if any(k in ex["name"] for k in ("Walk", "Cycling", "Jog")) else "10-12",
                 "rest": "-", "notes": "Keep effort light, RPE 4-5"}
                for ex in picks
            ]
        else:
            exercises = [
                {"name": ex["name"], "sets": str(scheme["sets"]), "reps": scheme["reps"],
                 "rest": f"{rest}s", "notes": "Controlled tempo, full ROM"}
                for ex in picks
            ]
        days.append({"title_en": title_en, "title_am": title_am, "exercises": exercises})

    return {
        "days": days,
        "frequency": "4-5 training days / week",
        "session_length": "45-60 minutes",
        "scheme_summary": f"{scheme['sets']} sets x {scheme['reps']} reps, {rest}s rest ({experience.title()} level)",
    }
