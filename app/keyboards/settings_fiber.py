from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_settings_fiber_keyboard(
    show_fiber: bool,
    language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "ru":
        enabled_text = (
            "✅ Показывать клетчатку"
            if show_fiber
            else "Показывать клетчатку"
        )
        disabled_text = (
            "❌ Скрывать клетчатку"
            if not show_fiber
            else "Скрывать клетчатку"
        )
        back_text = "⬅️ Назад к настройкам"
    else:
        enabled_text = (
            "✅ Show fiber"
            if show_fiber
            else "Show fiber"
        )
        disabled_text = (
            "❌ Hide fiber"
            if not show_fiber
            else "Hide fiber"
        )
        back_text = "⬅️ Back to settings"

    builder.button(
        text=enabled_text,
        callback_data="settings_fiber:on",
    )

    builder.button(
        text=disabled_text,
        callback_data="settings_fiber:off",
    )

    builder.button(
        text=back_text,
        callback_data="settings_fiber:back",
    )

    builder.adjust(1)

    return builder.as_markup()