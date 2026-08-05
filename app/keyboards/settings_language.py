from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_settings_language_keyboard(
    current_language: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    russian_text = (
        "✅ 🇷🇺 Русский"
        if current_language == "ru"
        else "🇷🇺 Русский"
    )

    english_text = (
        "✅ 🇬🇧 English"
        if current_language == "en"
        else "🇬🇧 English"
    )

    builder.button(
        text=russian_text,
        callback_data="settings_language:ru",
    )

    builder.button(
        text=english_text,
        callback_data="settings_language:en",
    )

    back_text = (
        "⬅️ Назад к настройкам"
        if current_language == "ru"
        else "⬅️ Back to settings"
    )

    builder.button(
        text=back_text,
        callback_data="settings_language:back",
    )

    builder.adjust(1)

    return builder.as_markup()