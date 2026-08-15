# -*- coding: utf-8 -*-
"""
Exercise library for SIMON ORIGIN TRANSFORMATION blueprint generator.

Each exercise is tagged so the workout builder can filter by:
- pattern: which training day / movement pattern it belongs to
- equipment: which equipment setups it works for ("home", "gym", "both",
  or "bodyweight" for zero-equipment options)
- injury_flags: body areas it should be EXCLUDED for if the client reports
  an injury/health issue mentioning that keyword
- level: minimum experience level it's appropriate for ("beginner",
  "intermediate", "advanced") -- beginner exercises are shown to everyone,
  advanced ones only to advanced clients.

"bodyweight" equipment exercises are always allowed regardless of the
client's equipment_available answer (they need nothing at all).
"""

EXERCISES = {
    "upper_strength": [
        {"name": "Barbell Bench Press", "equipment": "gym", "injury_flags": ["shoulder"], "level": "intermediate"},
        {"name": "Push-Up (feet elevated)", "equipment": "home", "injury_flags": ["shoulder", "wrist"], "level": "beginner"},
        {"name": "Standard Push-Up", "equipment": "bodyweight", "injury_flags": ["wrist"], "level": "beginner"},
        {"name": "Knee Push-Up", "equipment": "bodyweight", "injury_flags": ["wrist"], "level": "beginner"},
        {"name": "Dumbbell Shoulder Press", "equipment": "both", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Pike Push-Up", "equipment": "bodyweight", "injury_flags": ["shoulder", "wrist"], "level": "intermediate"},
        {"name": "Bent-Over Barbell Row", "equipment": "gym", "injury_flags": ["lower back"], "level": "intermediate"},
        {"name": "Single-Arm Dumbbell Row", "equipment": "both", "injury_flags": [], "level": "beginner"},
        {"name": "Lat Pulldown", "equipment": "gym", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Resistance Band Pull-Apart", "equipment": "home", "injury_flags": [], "level": "beginner"},
        {"name": "Incline Dumbbell Press", "equipment": "both", "injury_flags": ["shoulder"], "level": "intermediate"},
        {"name": "Plank Shoulder Tap", "equipment": "bodyweight", "injury_flags": ["wrist"], "level": "beginner"},
        {"name": "Superman Hold", "equipment": "bodyweight", "injury_flags": ["lower back"], "level": "beginner"},
        {"name": "Chair/Bench Dip", "equipment": "home", "injury_flags": ["shoulder", "elbow"], "level": "intermediate"},
        {"name": "Wide Push-Up", "equipment": "bodyweight", "injury_flags": ["shoulder", "wrist"], "level": "beginner"},
    ],
    "lower_core_strength": [
        {"name": "Barbell Back Squat", "equipment": "gym", "injury_flags": ["knee", "lower back"], "level": "intermediate"},
        {"name": "Goblet Squat", "equipment": "both", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Bodyweight Squat", "equipment": "bodyweight", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Romanian Deadlift (DB/BB)", "equipment": "both", "injury_flags": ["lower back"], "level": "intermediate"},
        {"name": "Walking Lunge", "equipment": "bodyweight", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Glute Bridge", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Hanging Knee Raise", "equipment": "gym", "injury_flags": ["shoulder"], "level": "intermediate"},
        {"name": "Dead Bug", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Plank Hold", "equipment": "bodyweight", "injury_flags": ["wrist"], "level": "beginner"},
        {"name": "Cable/Band Woodchopper", "equipment": "both", "injury_flags": ["lower back"], "level": "intermediate"},
        {"name": "Bicycle Crunch", "equipment": "bodyweight", "injury_flags": ["lower back"], "level": "beginner"},
        {"name": "Bird Dog", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Side Plank", "equipment": "bodyweight", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Mountain Climber", "equipment": "bodyweight", "injury_flags": ["wrist", "knee"], "level": "beginner"},
        {"name": "Hollow Body Hold", "equipment": "bodyweight", "injury_flags": ["lower back"], "level": "intermediate"},
    ],
    "active_recovery": [
        {"name": "Brisk Walk", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "World's Greatest Stretch", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Foam Rolling - Full Body", "equipment": "home", "injury_flags": [], "level": "beginner"},
        {"name": "Cat-Cow Mobility Flow", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "90/90 Hip Switch", "equipment": "bodyweight", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Band Shoulder Dislocates", "equipment": "home", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Light Cycling", "equipment": "gym", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Deep Breathing + Neck Mobility", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Standing Quad Stretch", "equipment": "bodyweight", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Thread the Needle Stretch", "equipment": "bodyweight", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Ankle Circles + Calf Stretch", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
    ],
    "push": [
        {"name": "Flat Barbell Bench Press", "equipment": "gym", "injury_flags": ["shoulder"], "level": "intermediate"},
        {"name": "Dumbbell Flat Press", "equipment": "both", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Seated Dumbbell Shoulder Press", "equipment": "both", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Incline Push-Up", "equipment": "bodyweight", "injury_flags": ["wrist"], "level": "beginner"},
        {"name": "Cable/Band Chest Fly", "equipment": "both", "injury_flags": ["shoulder"], "level": "intermediate"},
        {"name": "Lateral Raise", "equipment": "both", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Triceps Rope Pushdown", "equipment": "gym", "injury_flags": ["elbow"], "level": "beginner"},
        {"name": "Bench/Chair Dips", "equipment": "home", "injury_flags": ["shoulder", "elbow"], "level": "intermediate"},
        {"name": "Overhead Triceps Extension", "equipment": "both", "injury_flags": ["elbow"], "level": "beginner"},
        {"name": "Diamond Push-Up", "equipment": "bodyweight", "injury_flags": ["wrist", "elbow"], "level": "intermediate"},
        {"name": "Pike Push-Up", "equipment": "bodyweight", "injury_flags": ["shoulder", "wrist"], "level": "intermediate"},
        {"name": "Arnold Press", "equipment": "both", "injury_flags": ["shoulder"], "level": "intermediate"},
    ],
    "pull": [
        {"name": "Pull-Up / Assisted Pull-Up", "equipment": "gym", "injury_flags": ["shoulder"], "level": "intermediate"},
        {"name": "Band-Assisted Row", "equipment": "home", "injury_flags": [], "level": "beginner"},
        {"name": "Bent-Over Dumbbell Row", "equipment": "both", "injury_flags": ["lower back"], "level": "beginner"},
        {"name": "Seated Cable Row", "equipment": "gym", "injury_flags": ["lower back"], "level": "beginner"},
        {"name": "Face Pull", "equipment": "gym", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Dumbbell Bicep Curl", "equipment": "both", "injury_flags": ["elbow"], "level": "beginner"},
        {"name": "Hammer Curl", "equipment": "both", "injury_flags": ["elbow"], "level": "beginner"},
        {"name": "Reverse Fly", "equipment": "both", "injury_flags": ["shoulder"], "level": "beginner"},
        {"name": "Towel Row (door anchor)", "equipment": "home", "injury_flags": ["lower back"], "level": "beginner"},
        {"name": "Superman Row", "equipment": "bodyweight", "injury_flags": ["lower back"], "level": "beginner"},
        {"name": "Band Pull-Apart", "equipment": "home", "injury_flags": ["shoulder"], "level": "beginner"},
    ],
    "legs_glutes": [
        {"name": "Barbell Hip Thrust", "equipment": "gym", "injury_flags": ["lower back"], "level": "intermediate"},
        {"name": "Bodyweight Glute Bridge x1.5", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Bulgarian Split Squat", "equipment": "both", "injury_flags": ["knee"], "level": "intermediate"},
        {"name": "Leg Press", "equipment": "gym", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Step-Up (bench/box)", "equipment": "both", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Lying/Seated Leg Curl", "equipment": "gym", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Banded Lateral Walk", "equipment": "home", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Calf Raise", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Standing Hip Abduction (band)", "equipment": "home", "injury_flags": [], "level": "beginner"},
        {"name": "Single-Leg Glute Bridge", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Clamshell (band)", "equipment": "home", "injury_flags": [], "level": "beginner"},
        {"name": "Wall Sit", "equipment": "bodyweight", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Donkey Kick", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Sumo Squat", "equipment": "bodyweight", "injury_flags": ["knee"], "level": "beginner"},
    ],
    "rest_light_cardio": [
        {"name": "Easy Pace Walk / Jog", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Stationary Bike - Zone 2", "equipment": "gym", "injury_flags": ["knee"], "level": "beginner"},
        {"name": "Full-Body Stretch Flow", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Optional: Complete Rest", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
        {"name": "Easy Swim", "equipment": "gym", "injury_flags": [], "level": "beginner"},
        {"name": "Gentle Yoga Flow", "equipment": "bodyweight", "injury_flags": [], "level": "beginner"},
    ],
}

# Maps the 7-day split to (title_en, title_am, pattern_key)
DAY_PLAN = [
    ("Day 1: Upper Body Strength Focus", "1ኛ ቀን፡ የላይኛው አካል ጥንካሬ", "upper_strength"),
    ("Day 2: Lower Body & Core Strength", "2ኛ ቀን፡ የታችኛው አካል እና ኮር ጥንካሬ", "lower_core_strength"),
    ("Day 3: Active Recovery / Mobility", "3ኛ ቀን፡ ንቁ ማገገሚያ / እንቅስቃሴ", "active_recovery"),
    ("Day 4: Push Focus (Chest/Shoulders/Triceps)", "4ኛ ቀን፡ የግፊት ልምምድ", "push"),
    ("Day 5: Pull Focus (Back/Biceps)", "5ኛ ቀን፡ የመሳብ ልምምድ", "pull"),
    ("Day 6: Legs & Glutes", "6ኛ ቀን፡ እግር እና ዳሌ", "legs_glutes"),
    ("Day 7: Rest / Optional Light Cardio", "7ኛ ቀን፡ እረፍት / ቀላል ካርዲዮ", "rest_light_cardio"),
]
