from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_product_results_keyboard(
    products: list[dict],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for index, product in enumerate(products):
        name = product["name"]
        brand = product.get("brand")

        if brand:
            text = f"{name} — {brand}"
        else:
            text = name

        builder.button(
            text=text[:60],
            callback_data=f"product_search:{index}",
        )

    retry_text = (
        "🔎 Другой запрос"
        if language == "ru"
        else "🔎 Another search"
    )

    builder.button(
        text=retry_text,
        callback_data="product_search:retry",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_selected_product_keyboard(
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    favorite_text = (
        "⭐ Добавить в избранное"
        if language == "ru"
        else "⭐ Add to favorites"
    )

    continue_text = (
        "⚖️ Ввести количество"
        if language == "ru"
        else "⚖️ Enter amount"
    )

    builder.button(
        text=favorite_text,
        callback_data="product_search:add_favorite",
    )

    builder.button(
        text=continue_text,
        callback_data="product_search:enter_amount",
    )

    builder.adjust(1)

    return builder.as_markup()