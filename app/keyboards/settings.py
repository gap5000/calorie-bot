from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_settings_keyboard(
    language: str,
) -> ReplyKeyboardMarkup:
    if language == "ru":
        language_text = "🌍 Язык"
        fiber_text = "🌾 Клетчатка"
        units_text = "⚖️ Единицы измерения"
        notifications_text = "🔔 Уведомления"
        profile_text = "👤 Профиль"
        calculate_norm_text = "🔥 Рассчитать норму"
        back_text = "⬅️ Главное меню"
    else:
        language_text = "🌍 Language"
        fiber_text = "🌾 Fiber"
        units_text = "⚖️ Units"
        notifications_text = "🔔 Notifications"
        profile_text = "👤 Profile"
        calculate_norm_text = "🔥 Calculate daily needs"
        back_text = "⬅️ Main menu"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=language_text),
                KeyboardButton(text=fiber_text),
            ],
            [
                KeyboardButton(text=units_text),
                KeyboardButton(text=notifications_text),
            ],
            [
                KeyboardButton(text=profile_text),
            ],
            [
                KeyboardButton(text=calculate_norm_text),
            ],
            [
                KeyboardButton(text=back_text),
            ],
        ],
        resize_keyboard=True,
    )