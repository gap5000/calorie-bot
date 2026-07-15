from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales.texts import get_text


def get_nutrition_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    back_text = (
        "⬅️ Главное меню"
        if language == "ru"
        else "⬅️ Main menu"
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=get_text("add_nutrition", language)
                ),
            ],
            [
                KeyboardButton(
                    text=get_text("search_product", language)
                ),
                KeyboardButton(
                    text=get_text("add_by_barcode", language)
                ),
            ],
            [
                KeyboardButton(
                    text=get_text(
                        "nutrition_history",
                        language,
                    )
                ),
            ],
            [
                KeyboardButton(text=back_text),
            ],
        ],
        resize_keyboard=True,
    )