from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_barcode_method_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    if language == "ru":
        photo_text = "📷 Отправить фото"
        digits_text = "⌨️ Ввести цифры"
    else:
        photo_text = "📷 Send photo"
        digits_text = "⌨️ Enter digits"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=photo_text,
                    callback_data="barcode_method:photo",
                )
            ],
            [
                InlineKeyboardButton(
                    text=digits_text,
                    callback_data="barcode_method:digits",
                )
            ],
        ]
    )