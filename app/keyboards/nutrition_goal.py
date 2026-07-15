from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.keyboards.main import get_main_keyboard

def get_goal_period_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        buttons = [
            ("📅 1 день", "day"),
            ("🗓 1 неделя", "week"),
            ("📆 30 дней", "month"),
            ("♾ Пока не изменю", "unlimited"),
        ]
    else:
        buttons = [
            ("📅 1 day", "day"),
            ("🗓 1 week", "week"),
            ("📆 30 days", "month"),
            ("♾ Until I change it", "unlimited"),
        ]

    for text, period in buttons:
        builder.button(
            text=text,
            callback_data=f"goal_period:{period}",
        )

    builder.adjust(1)

    return builder.as_markup()