from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry


def get_nutrition_history_keyboard(
    entries: list[NutritionEntry],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for entry in entries:
        entry_name = entry.name or "Food"

        button_text = get_text(
            "nutrition_delete_button",
            language,
        ).format(
            name=entry_name[:30],
            calories=entry.calories,
        )

        builder.button(
            text=button_text,
            callback_data=f"nutrition_delete:{entry.id}",
        )

    builder.adjust(1)

    return builder.as_markup()