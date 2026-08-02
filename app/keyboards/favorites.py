from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.favorite_product import FavoriteProduct


def get_favorites_keyboard(
    favorites: list[FavoriteProduct],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for favorite in favorites:
        product = favorite.product

        if product.brand:
            button_text = (
                f"{product.name} — {product.brand}"
            )
        else:
            button_text = product.name

        builder.button(
            text=button_text[:60],
            callback_data=(
                f"favorite:select:{product.id}"
            ),
        )

    if favorites:
        remove_text = (
            "🗑 Удалить из избранного"
            if language == "ru"
            else "🗑 Remove from favorites"
        )

        builder.button(
            text=remove_text,
            callback_data="favorite:remove_menu",
        )

    back_text = (
        "⬅️ Назад к питанию"
        if language == "ru"
        else "⬅️ Back to nutrition"
    )

    builder.button(
        text=back_text,
        callback_data="favorite:back",
    )

    builder.adjust(1)

    return builder.as_markup()


def get_remove_favorites_keyboard(
    favorites: list[FavoriteProduct],
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for favorite in favorites:
        product = favorite.product

        if product.brand:
            button_text = (
                f"🗑 {product.name} — {product.brand}"
            )
        else:
            button_text = f"🗑 {product.name}"

        builder.button(
            text=button_text[:60],
            callback_data=(
                f"favorite:remove:{product.id}"
            ),
        )

    back_text = (
        "⬅️ Назад к избранному"
        if language == "ru"
        else "⬅️ Back to favorites"
    )

    builder.button(
        text=back_text,
        callback_data="favorite:remove_back",
    )

    builder.adjust(1)

    return builder.as_markup()