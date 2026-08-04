from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.locales.texts import get_text


def get_main_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    dishes_text = (
        "🍲 Мои блюда"
        if language == "ru"
        else "🍲 My dishes"
    )

    settings_text = (
        "⚙️ Настройки"
        if language == "ru"
        else "⚙️ Settings"
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=get_text("nutrition", language)
                ),
                KeyboardButton(
                    text=get_text("progress", language)
                ),
            ],
            [
                KeyboardButton(
                    text=get_text("workout", language)
                ),
                KeyboardButton(
                    text=dishes_text
                ),
            ],
            [
                KeyboardButton(
                    text=get_text("set_goal", language)
                ),
                KeyboardButton(
                    text=settings_text
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