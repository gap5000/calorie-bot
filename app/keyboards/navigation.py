from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_back_to_main_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    button_text = (
        "⬅️ Главное меню"
        if language == "ru"
        else "⬅️ Main menu"
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_text)]
        ],
        resize_keyboard=True,
    )