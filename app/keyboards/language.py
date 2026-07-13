from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

language_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data="language:ru",
            ),
            InlineKeyboardButton(
                text="🇬🇧 English",
                callback_data="language:en",
            ),
        ]
    ]
)