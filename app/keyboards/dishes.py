from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.dish import Dish


def get_dishes_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    if language == "ru":
        create_text = "➕ Создать блюдо"
        saved_text = "📖 Сохранённые блюда"
        back_text = "⬅️ Главное меню"
    else:
        create_text = "➕ Create dish"
        saved_text = "📖 Saved dishes"
        back_text = "⬅️ Main menu"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=create_text),
            ],
            [
                KeyboardButton(text=saved_text),
            ],
            [
                KeyboardButton(text=back_text),
            ],
        ],
        resize_keyboard=True,
    )


def get_saved_dishes_keyboard(
    dishes: list[Dish],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for dish in dishes:
        builder.button(
            text=f"🍲 {dish.name}"[:64],
            callback_data=f"dish:select:{dish.id}",
        )

    back_text = (
        "⬅️ Назад к блюдам"
        if language == "ru"
        else "⬅️ Back to dishes"
    )

    builder.button(
        text=back_text,
        callback_data="dish:back_to_menu",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_dish_actions_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        add_ingredient_text = "➕ Добавить ингредиент"
        add_to_diary_text = "📥 Добавить в питание"
        edit_text = "✏️ Редактировать"
        delete_text = "🗑 Удалить блюдо"
        back_text = "⬅️ К сохранённым блюдам"
    else:
        add_ingredient_text = "➕ Add ingredient"
        add_to_diary_text = "📥 Add to nutrition"
        edit_text = "✏️ Edit"
        delete_text = "🗑 Delete dish"
        back_text = "⬅️ Back to saved dishes"

    builder.button(
        text=add_ingredient_text,
        callback_data="dish:add_ingredient",
    )

    builder.button(
        text=add_to_diary_text,
        callback_data="dish:add_to_diary",
    )

    builder.button(
        text=edit_text,
        callback_data="dish:edit",
    )

    builder.button(
        text=delete_text,
        callback_data="dish:delete",
    )

    builder.button(
        text=back_text,
        callback_data="dish:list",
    )

    builder.adjust(1)

    return builder.as_markup()