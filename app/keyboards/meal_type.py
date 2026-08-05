from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_meal_type_keyboard(
    language: str,
    callback_prefix: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        breakfast_text = "🍳 Завтрак"
        lunch_text = "🍲 Обед"
        dinner_text = "🍽 Ужин"
        snack_text = "🍎 Перекус"
        cancel_text = "❌ Отмена"
    else:
        breakfast_text = "🍳 Breakfast"
        lunch_text = "🍲 Lunch"
        dinner_text = "🍽 Dinner"
        snack_text = "🍎 Snack"
        cancel_text = "❌ Cancel"

    builder.button(
        text=breakfast_text,
        callback_data=f"{callback_prefix}:breakfast",
    )
    builder.button(
        text=lunch_text,
        callback_data=f"{callback_prefix}:lunch",
    )
    builder.button(
        text=dinner_text,
        callback_data=f"{callback_prefix}:dinner",
    )
    builder.button(
        text=snack_text,
        callback_data=f"{callback_prefix}:snack",
    )
    builder.button(
        text=cancel_text,
        callback_data=f"{callback_prefix}:cancel",
    )

    builder.adjust(2, 2, 1)

    return builder.as_markup()