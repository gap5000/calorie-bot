from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_back_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    text = (
        "⬅️ Назад"
        if language == "ru"
        else "⬅️ Back"
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=text),
            ],
        ],
        resize_keyboard=True,
    )


def get_entry_finished_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    favorite = (
        "⭐ Добавить в избранное"
        if language == "ru"
        else "⭐ Add to favorites"
    )

    again = (
        "➕ Добавить ещё"
        if language == "ru"
        else "➕ Add another"
    )

    finish = (
        "⬅️ К разделу питания"
        if language == "ru"
        else "⬅️ Back to nutrition"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=favorite,
                    callback_data="manual:add_favorite",
                )
            ],
            [
                InlineKeyboardButton(
                    text=again,
                    callback_data="manual:add_again",
                )
            ],
            [
                InlineKeyboardButton(
                    text=finish,
                    callback_data="manual:finish",
                )
            ],
        ]
    )