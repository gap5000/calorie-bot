from typing import TypedDict


class ExerciseData(TypedDict):
    category: str
    ru: str
    en: str


CATEGORIES = {
    "chest": {
        "ru": "🟥 Грудь",
        "en": "🟥 Chest",
    },
    "back": {
        "ru": "🟦 Спина",
        "en": "🟦 Back",
    },
    "legs": {
        "ru": "🟩 Ноги",
        "en": "🟩 Legs",
    },
    "shoulders": {
        "ru": "🟨 Плечи",
        "en": "🟨 Shoulders",
    },
    "biceps": {
        "ru": "💪 Бицепс",
        "en": "💪 Biceps",
    },
    "triceps": {
        "ru": "🔱 Трицепс",
        "en": "🔱 Triceps",
    },
    "abs": {
        "ru": "🟪 Пресс",
        "en": "🟪 Abs",
    },
}


EXERCISES: dict[str, ExerciseData] = {
    # Грудь
    "barbell_bench_press": {
        "category": "chest",
        "ru": "Жим штанги лёжа",
        "en": "Barbell bench press",
    },
    "dumbbell_bench_press": {
        "category": "chest",
        "ru": "Жим гантелей лёжа",
        "en": "Dumbbell bench press",
    },
    "incline_bench_press": {
        "category": "chest",
        "ru": "Жим на наклонной скамье",
        "en": "Incline bench press",
    },
    "chest_dips": {
        "category": "chest",
        "ru": "Отжимания на брусьях",
        "en": "Chest dips",
    },
    "chest_fly": {
        "category": "chest",
        "ru": "Сведение рук",
        "en": "Chest fly",
    },

    # Спина
    "pull_ups": {
        "category": "back",
        "ru": "Подтягивания",
        "en": "Pull-ups",
    },
    "lat_pulldown": {
        "category": "back",
        "ru": "Тяга верхнего блока",
        "en": "Lat pulldown",
    },
    "barbell_row": {
        "category": "back",
        "ru": "Тяга штанги в наклоне",
        "en": "Barbell row",
    },
    "seated_cable_row": {
        "category": "back",
        "ru": "Тяга горизонтального блока",
        "en": "Seated cable row",
    },
    "deadlift": {
        "category": "back",
        "ru": "Становая тяга",
        "en": "Deadlift",
    },

    # Ноги
    "barbell_squat": {
        "category": "legs",
        "ru": "Приседания со штангой",
        "en": "Barbell squat",
    },
    "leg_press": {
        "category": "legs",
        "ru": "Жим ногами",
        "en": "Leg press",
    },
    "leg_extension": {
        "category": "legs",
        "ru": "Разгибание ног",
        "en": "Leg extension",
    },
    "leg_curl": {
        "category": "legs",
        "ru": "Сгибание ног",
        "en": "Leg curl",
    },
    "lunges": {
        "category": "legs",
        "ru": "Выпады",
        "en": "Lunges",
    },
    "calf_raise": {
        "category": "legs",
        "ru": "Подъёмы на носки",
        "en": "Calf raise",
    },

    # Плечи
    "overhead_press": {
        "category": "shoulders",
        "ru": "Жим штанги стоя",
        "en": "Overhead press",
    },
    "dumbbell_shoulder_press": {
        "category": "shoulders",
        "ru": "Жим гантелей сидя",
        "en": "Dumbbell shoulder press",
    },
    "lateral_raise": {
        "category": "shoulders",
        "ru": "Махи гантелями в стороны",
        "en": "Lateral raise",
    },
    "rear_delt_fly": {
        "category": "shoulders",
        "ru": "Разведение на заднюю дельту",
        "en": "Rear delt fly",
    },

    # Бицепс
    "barbell_curl": {
        "category": "biceps",
        "ru": "Подъём штанги на бицепс",
        "en": "Barbell curl",
    },
    "dumbbell_curl": {
        "category": "biceps",
        "ru": "Подъём гантелей на бицепс",
        "en": "Dumbbell curl",
    },
    "hammer_curl": {
        "category": "biceps",
        "ru": "Молотковые сгибания",
        "en": "Hammer curl",
    },
    "preacher_curl": {
        "category": "biceps",
        "ru": "Сгибания на скамье Скотта",
        "en": "Preacher curl",
    },

    # Трицепс
    "triceps_pushdown": {
        "category": "triceps",
        "ru": "Разгибание рук на блоке",
        "en": "Triceps pushdown",
    },
    "close_grip_bench_press": {
        "category": "triceps",
        "ru": "Жим узким хватом",
        "en": "Close-grip bench press",
    },
    "skull_crusher": {
        "category": "triceps",
        "ru": "Французский жим",
        "en": "Skull crusher",
    },
    "overhead_triceps_extension": {
        "category": "triceps",
        "ru": "Разгибание из-за головы",
        "en": "Overhead triceps extension",
    },

    # Пресс
    "crunches": {
        "category": "abs",
        "ru": "Скручивания",
        "en": "Crunches",
    },
    "hanging_leg_raise": {
        "category": "abs",
        "ru": "Подъём ног в висе",
        "en": "Hanging leg raise",
    },
    "plank": {
        "category": "abs",
        "ru": "Планка",
        "en": "Plank",
    },
    "cable_crunch": {
        "category": "abs",
        "ru": "Скручивания на блоке",
        "en": "Cable crunch",
    },
}


def get_exercise_name(
    exercise_code: str,
    language: str,
) -> str | None:
    exercise = EXERCISES.get(exercise_code)

    if exercise is None:
        return None

    selected_language = language if language in {"ru", "en"} else "en"

    return exercise[selected_language]