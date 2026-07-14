from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.data.exercises import CATEGORIES, EXERCISES


def get_categories_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    selected_language = language if language in {"ru", "en"} else "en"

    builder = InlineKeyboardBuilder()

    for category_code, translations in CATEGORIES.items():
        builder.button(
            text=translations[selected_language],
            callback_data=f"workout_category:{category_code}",
        )

    custom_text = (
        "✍️ Ввести своё упражнение"
        if selected_language == "ru"
        else "✍️ Enter custom exercise"
    )

    builder.button(
        text=custom_text,
        callback_data="workout_exercise:custom",
    )

    builder.adjust(2, 2, 2, 1, 1)

    return builder.as_markup()


def get_exercises_keyboard(
    category: str,
    language: str,
) -> InlineKeyboardMarkup:
    selected_language = language if language in {"ru", "en"} else "en"

    builder = InlineKeyboardBuilder()

    for exercise_code, exercise in EXERCISES.items():
        if exercise["category"] != category:
            continue

        builder.button(
            text=exercise[selected_language],
            callback_data=f"workout_exercise:{exercise_code}",
        )

    custom_text = (
        "✍️ Ввести своё"
        if selected_language == "ru"
        else "✍️ Enter custom"
    )
    back_text = (
        "⬅️ Назад"
        if selected_language == "ru"
        else "⬅️ Back"
    )

    builder.button(
        text=custom_text,
        callback_data="workout_exercise:custom",
    )
    builder.button(
        text=back_text,
        callback_data="workout:back_to_categories",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_workout_actions_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    selected_language = language if language in {"ru", "en"} else "en"

    builder = InlineKeyboardBuilder()

    if selected_language == "ru":
        same_exercise = "➕ Ещё подход"
        new_exercise = "🔄 Другое упражнение"
        finish = "✅ Завершить тренировку"
    else:
        same_exercise = "➕ Another set"
        new_exercise = "🔄 New exercise"
        finish = "✅ Finish workout"

    builder.button(
        text=same_exercise,
        callback_data="workout:same_exercise",
    )
    builder.button(
        text=new_exercise,
        callback_data="workout:new_exercise",
    )
    builder.button(
        text=finish,
        callback_data="workout:finish",
    )

    builder.adjust(1)

    return builder.as_markup()