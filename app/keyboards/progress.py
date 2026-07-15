from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales.texts import get_text


def get_progress_keyboard(
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
                    text=get_text("progress_today", language)
                )
            ],
            [
                KeyboardButton(
                    text=get_text("progress_week", language)
                ),
                KeyboardButton(
                    text=get_text("progress_month", language)
                ),
            ],
            [
                KeyboardButton(text=back_text)
            ],
        ],
        resize_keyboard=True,
    )