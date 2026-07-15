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