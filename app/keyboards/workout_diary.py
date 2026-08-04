from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.workouts import WorkoutDiaryEntry


def get_workout_diary_keyboard(
    entries: list[WorkoutDiaryEntry],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if entries:
        delete_text = (
            "🗑 Удалить запись"
            if language == "ru"
            else "🗑 Delete entry"
        )

        builder.button(
            text=delete_text,
            callback_data="workout_diary:delete_menu",
        )

    back_text = (
        "⬅️ Назад к силовым"
        if language == "ru"
        else "⬅️ Back to strength"
    )

    builder.button(
        text=back_text,
        callback_data="workout_diary:back",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_delete_workout_entries_keyboard(
    entries: list[WorkoutDiaryEntry],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    unit = "кг" if language == "ru" else "kg"

    for entry in entries:
        date_text = entry["created_at"].strftime(
            "%d.%m.%Y"
        )

        weight = format_number(
            entry["weight"]
        )

        button_text = (
            f"🗑 {date_text} — "
            f"{entry['exercise_name']} — "
            f"{weight} {unit} × "
            f"{entry['repetitions']}"
        )

        builder.button(
            text=button_text[:64],
            callback_data=(
                "workout_diary:delete:"
                f"{entry['workout_set_id']}"
            ),
        )

    back_text = (
        "⬅️ Назад к дневнику"
        if language == "ru"
        else "⬅️ Back to diary"
    )

    builder.button(
        text=back_text,
        callback_data="workout_diary:list",
    )

    builder.adjust(1)

    return builder.as_markup()


def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"