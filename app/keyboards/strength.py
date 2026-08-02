from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_strength_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    if language == "ru":
        exercises = "🏋️ Мои упражнения"
        diary = "📓 Дневник тренировок"
        progression = "📈 Прогрессия нагрузки"
        records = "🏆 Личные рекорды"
        back = "⬅️ Главное меню"
    else:
        exercises = "🏋️ My exercises"
        diary = "📓 Workout diary"
        progression = "📈 Load progression"
        records = "🏆 Personal records"
        back = "⬅️ Main menu"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=exercises),
            ],
            [
                KeyboardButton(text=diary),
                KeyboardButton(text=progression),
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