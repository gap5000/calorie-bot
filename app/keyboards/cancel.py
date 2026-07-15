from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales.texts import get_text


def get_cancel_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=get_text("cancel", language)
                )
            ]
        ],
        resize_keyboard=True,
    )