from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_strength_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    if language == "ru":
        start_workout = "🏋️ Начать тренировку"
        exercises = "📋 Мои упражнения"
        history = "📖 История тренировок"
        records = "🏆 Личные рекорды"
        back = "⬅️ Главное меню"
    else:
        start_workout = "🏋️ Start workout"
        exercises = "📋 My exercises"
        history = "📖 Workout history"
        records = "🏆 Personal records"
        back = "⬅️ Main menu"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=start_workout),
            ],
            [
                KeyboardButton(text=exercises),
                KeyboardButton(text=history),
            ],
            [
                KeyboardButton(text=records),
            ],
            [
                KeyboardButton(text=back),
            ],
        ],
        resize_keyboard=True,
    )