from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_barcode_product_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        favorite_text = "⭐ Добавить в избранное"
        amount_text = "⚖️ Ввести количество"
    else:
        favorite_text = "⭐ Add to favorites"
        amount_text = "⚖️ Enter amount"

    builder.button(
        text=favorite_text,
        callback_data="barcode:add_favorite",
    )

    builder.button(
        text=amount_text,
        callback_data="barcode:enter_amount",
    )

    builder.adjust(1)

    return builder.as_markup()