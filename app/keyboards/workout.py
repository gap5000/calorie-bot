from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_workout_actions_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    if language == "ru":
        same_exercise = "➕ Ещё подход"
        new_exercise = "🔄 Другое упражнение"
        finish = "✅ Завершить тренировку"
    else:
        same_exercise = "➕ Another set"
        new_exercise = "🔄 New exercise"
        finish = "✅ Finish workout"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=same_exercise,
                    callback_data="workout:same_exercise",
                )
            ],
            [
                InlineKeyboardButton(
                    text=new_exercise,
                    callback_data="workout:new_exercise",
                )
            ],
            [
                InlineKeyboardButton(
                    text=finish,
                    callback_data="workout:finish",
                )
            ],
        ]
    )