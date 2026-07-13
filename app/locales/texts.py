TRANSLATIONS = {
    "ru": {
        "choose_language": (
            "🌍 <b>Выберите язык</b>\n\n"
            "Язык можно будет изменить позже в настройках."
        ),
        "main_menu": (
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите нужное действие."
        ),
        "metabolism_intro": (
        "🔥 <b>Расчёт дневной нормы</b>\n\n"
        "Ответьте на несколько вопросов. "
        "Результат будет ориентировочным.\n\n"
        "Шаг 1 из 5: выберите пол."
        ),
        "enter_age": "Шаг 2 из 5\n\n🎂 Введите ваш возраст:",
        "enter_height": "Шаг 3 из 5\n\n📏 Введите рост в сантиметрах:",
        "enter_weight": "Шаг 4 из 5\n\n⚖️ Введите вес в килограммах:",
        "choose_activity": (
        "Шаг 5 из 5\n\n"
        "🚶 Выберите примерный уровень активности:"
        ),
        "invalid_age": "Введите возраст целым числом от 14 до 100.",
        "invalid_height": "Введите рост числом от 100 до 250 см.",
        "invalid_weight": "Введите вес числом от 30 до 350 кг.",
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
        "main_menu": (
        "🏠 <b>Main menu</b>\n\n"
        "Choose an action."
        ),
        "metabolism_intro": (
        "🔥 <b>Daily calorie calculation</b>\n\n"
        "Answer a few questions. "
        "The result will be an estimate.\n\n"
        "Step 1 of 5: choose your sex."
        ),
        "enter_age": "Step 2 of 5\n\n🎂 Enter your age:",
        "enter_height": (
        "Step 3 of 5\n\n"
        "📏 Enter your height in centimetres:"
        ),
        "enter_weight": (
        "Step 4 of 5\n\n"
        "⚖️ Enter your weight in kilograms:"
        ),
        "choose_activity": (
        "Step 5 of 5\n\n"
        "🚶 Choose your approximate activity level:"
        ),
        "invalid_age": "Enter a whole-number age between 14 and 100.",
        "invalid_height": "Enter a height between 100 and 250 cm.",
        "invalid_weight": "Enter a weight between 30 and 350 kg.",
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