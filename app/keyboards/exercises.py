from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.exercise import Exercise


def get_exercises_keyboard(
    exercises: list[Exercise],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for exercise in exercises:
        builder.button(
            text=f"🏋️ {exercise.name}"[:60],
            callback_data=f"exercise:select:{exercise.id}",
        )

    add_text = (
        "➕ Добавить упражнение"
        if language == "ru"
        else "➕ Add exercise"
    )

    builder.button(
        text=add_text,
        callback_data="exercise:add",
    )

    if exercises:
        delete_text = (
            "🗑 Удалить упражнение"
            if language == "ru"
            else "🗑 Delete exercise"
        )

        builder.button(
            text=delete_text,
            callback_data="exercise:delete_menu",
        )

    back_text = (
        "⬅️ Назад к силовым"
        if language == "ru"
        else "⬅️ Back to strength"
    )

    builder.button(
        text=back_text,
        callback_data="exercise:back",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_exercise_actions_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        add_result_text = "➕ Добавить результат"
        history_text = "📓 История упражнения"
        progression_text = "📈 Прогресс"
        record_text = "🏆 Личный рекорд"
        back_text = "⬅️ К упражнениям"
    else:
        add_result_text = "➕ Add result"
        history_text = "📓 Exercise history"
        progression_text = "📈 Progress"
        record_text = "🏆 Personal record"
        back_text = "⬅️ Back to exercises"

    builder.button(
        text=add_result_text,
        callback_data="exercise:add_result",
    )

    builder.button(
        text=history_text,
        callback_data="exercise:history",
    )

    builder.button(
        text=progression_text,
        callback_data="exercise:progression",
    )

    builder.button(
        text=record_text,
        callback_data="exercise:record",
    )

    builder.button(
        text=back_text,
        callback_data="exercise:list",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_delete_exercises_keyboard(
    exercises: list[Exercise],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for exercise in exercises:
        builder.button(
            text=f"🗑 {exercise.name}"[:60],
            callback_data=f"exercise:delete:{exercise.id}",
        )

    back_text = (
        "⬅️ Назад к упражнениям"
        if language == "ru"
        else "⬅️ Back to exercises"
    )

    builder.button(
        text=back_text,
        callback_data="exercise:list",
    )

    builder.adjust(1)

    return builder.as_markup()