TRANSLATIONS = {
    "ru": {
        "choose_language": (
            "🌍 <b>Выберите язык</b>\n\n"
            "Язык можно будет изменить позже в настройках."
        ),
        "welcome": (
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Я помогу вам считать калории и БЖУ, "
            "следить за дневной целью и записывать тренировки."
        ),
        "set_goal": "🎯 Настроить цель КБЖУ",
        "add_nutrition": "➕ Добавить питание",
        "today": "📊 Сегодня",
        "calculate_norm": "🔥 Рассчитать норму",
        "workout": "🏋️ Силовая тренировка",
        "features": "ℹ️ Возможности бота",
    },
    "en": {
        "choose_language": (
            "🌍 <b>Choose your language</b>\n\n"
            "You will be able to change it later in settings."
        ),
        "welcome": (
            "👋 <b>Welcome!</b>\n\n"
            "I will help you track calories and macros, "
            "follow your daily goals, and log workouts."
        ),
        "set_goal": "🎯 Set calorie and macro goals",
        "add_nutrition": "➕ Add nutrition",
        "today": "📊 Today",
        "calculate_norm": "🔥 Calculate daily needs",
        "workout": "🏋️ Strength workout",
        "features": "ℹ️ Bot features",
    },
}

def get_text(key: str, language: str = "en") -> str:
    selected_language = language if language in TRANSLATIONS else "en"

    return TRANSLATIONS[selected_language].get(
        key,
        TRANSLATIONS["en"].get(key, key),
    )