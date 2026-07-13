from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales.texts import get_text


def get_main_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=get_text("set_goal", language)
                )
            ],
            [
                KeyboardButton(
                    text=get_text("add_nutrition", language)
                ),
                KeyboardButton(
                    text=get_text("today", language)
                ),
            ],
            [
                KeyboardButton(
                    text=get_text("calculate_norm", language)
                ),
            ],
            [
                KeyboardButton(
                    text=get_text("workout", language)
                ),
            ],
            [
                KeyboardButton(
                    text=get_text("features", language)
                ),
            ],
        ],
        resize_keyboard=True,
    )