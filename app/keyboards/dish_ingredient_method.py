from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_dish_ingredient_method_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        search_text = "🔎 По названию"
        barcode_text = "📷 По штрихкоду"
        favorites_text = "⭐ Из избранного"
        back_text = "⬅️ Назад к блюду"
    else:
        search_text = "🔎 Search by name"
        barcode_text = "📷 Scan barcode"
        favorites_text = "⭐ From favorites"
        back_text = "⬅️ Back to dish"

    builder.button(
        text=search_text,
        callback_data="dish_ingredient:search",
    )

    builder.button(
        text=barcode_text,
        callback_data="dish_ingredient:barcode",
    )

    builder.button(
        text=favorites_text,
        callback_data="dish_ingredient:favorites",
    )

    builder.button(
        text=back_text,
        callback_data="dish_ingredient:back",
    )

    builder.adjust(1)

    return builder.as_markup()