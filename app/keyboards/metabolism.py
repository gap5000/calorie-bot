from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


gender_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👨 Мужчина / Male",
                callback_data="metabolism_gender:male",
            ),
            InlineKeyboardButton(
                text="👩 Женщина / Female",
                callback_data="metabolism_gender:female",
            ),
        ]
    ]
)


activity_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🪑 Минимальная / Sedentary",
                callback_data="metabolism_activity:sedentary",
            )
        ],
        [
            InlineKeyboardButton(
                text="🚶 Лёгкая / Light",
                callback_data="metabolism_activity:light",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏃 Средняя / Moderate",
                callback_data="metabolism_activity:moderate",
            )
        ],
        [
            InlineKeyboardButton(
                text="💪 Высокая / High",
                callback_data="metabolism_activity:high",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔥 Очень высокая / Very high",
                callback_data="metabolism_activity:very_high",
            )
        ],
    ]
)