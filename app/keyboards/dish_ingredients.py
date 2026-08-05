from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.product import Product


def get_dish_ingredient_products_keyboard(
    products: list[Product],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for product in products:
        product_text = product.name

        if product.brand:
            product_text = (
                f"{product.name} — {product.brand}"
            )

        builder.button(
            text=f"🥗 {product_text}"[:64],
            callback_data=(
                f"dish:ingredient_product:{product.id}"
            ),
        )

    back_text = (
        "⬅️ Назад к блюду"
        if language == "ru"
        else "⬅️ Back to dish"
    )

    builder.button(
        text=back_text,
        callback_data="dish:ingredient_back",
    )

    builder.adjust(1)

    return builder.as_markup()