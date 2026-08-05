from app.keyboards.settings_fiber import (
    get_settings_fiber_keyboard,
)
from app.services.user_settings import (
    get_or_create_user_settings,
)
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.settings_language import (
    get_settings_language_keyboard,
)
from app.models.user import User
from aiogram import F, Router
from aiogram.fsm.context import FSMContext

from app.keyboards.main import get_main_keyboard
from app.keyboards.settings import get_settings_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "⚙️ Настройки",
            "⚙️ Settings",
        }
    )
)
async def settings_menu_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()

    text = (
        "⚙️ <b>Настройки</b>\n\n"
        "Выберите нужный раздел:"
        if language == "ru"
        else (
            "⚙️ <b>Settings</b>\n\n"
            "Choose a section:"
        )
    )

    await message.answer(
        text,
        reply_markup=get_settings_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "🌍 Язык",
            "🌍 Language",
        }
    )
)
async def language_settings_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    text = (
        "🌍 <b>Язык</b>\n\n"
        "Выберите язык интерфейса:"
        if language == "ru"
        else (
            "🌍 <b>Language</b>\n\n"
            "Choose the interface language:"
        )
    )

    await message.answer(
        text,
        reply_markup=get_settings_language_keyboard(
            current_language=language,
        ),
    )

@router.callback_query(
    F.data.in_(
        {
            "settings_language:ru",
            "settings_language:en",
        }
    )
)
async def change_language_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    new_language = callback.data.split(":")[1]

    if new_language not in {"ru", "en"}:
        await callback.answer()
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "User account was not found",
                show_alert=True,
            )
            return

        user.language = new_language
        await session.commit()

    await state.clear()
    await callback.answer()

    if callback.message:
        text = (
            "✅ <b>Язык изменён</b>\n\n"
            "Интерфейс теперь отображается на русском языке."
            if new_language == "ru"
            else (
                "✅ <b>Language changed</b>\n\n"
                "The interface is now displayed in English."
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_settings_language_keyboard(
                current_language=new_language,
            ),
        )

        await callback.message.answer(
            (
                "⚙️ <b>Настройки</b>\n\n"
                "Выберите нужный раздел:"
                if new_language == "ru"
                else (
                    "⚙️ <b>Settings</b>\n\n"
                    "Choose a section:"
                )
            ),
            reply_markup=get_settings_keyboard(
                new_language
            ),
        )

@router.callback_query(
    F.data == "settings_language:back"
)
async def back_from_language_settings(
    callback: CallbackQuery,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            (
                "⚙️ <b>Настройки</b>\n\n"
                "Выберите нужный раздел:"
                if language == "ru"
                else (
                    "⚙️ <b>Settings</b>\n\n"
                    "Choose a section:"
                )
            ),
            reply_markup=get_settings_keyboard(language),
        )

@router.message(
    F.text.in_(
        {
            "🌾 Клетчатка",
            "🌾 Fiber",
        }
    )
)
async def fiber_settings_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "User account was not found. Send /start."
            )
            return

        settings = await get_or_create_user_settings(
            session=session,
            user_id=user.id,
        )

        await session.commit()

    status_text = (
        "включено" if settings.show_fiber else "выключено"
    )

    if language == "ru":
        text = (
            "🌾 <b>Клетчатка</b>\n\n"
            f"Текущее состояние: <b>{status_text}</b>\n\n"
            "Выберите, показывать ли клетчатку "
            "в продуктах, дневнике и блюдах."
        )
    else:
        status_text = (
            "enabled"
            if settings.show_fiber
            else "disabled"
        )

        text = (
            "🌾 <b>Fiber</b>\n\n"
            f"Current status: <b>{status_text}</b>\n\n"
            "Choose whether fiber should be shown "
            "in products, diary entries, and dishes."
        )

    await message.answer(
        text,
        reply_markup=get_settings_fiber_keyboard(
            show_fiber=settings.show_fiber,
            language=language,
        ),
    )

@router.callback_query(
    F.data.in_(
        {
            "settings_fiber:on",
            "settings_fiber:off",
        }
    )
)
async def change_fiber_setting(
    callback: CallbackQuery,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    language = await get_user_language(
        callback.from_user.id
    )

    show_fiber = callback.data == "settings_fiber:on"

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "User account was not found",
                show_alert=True,
            )
            return

        settings = await get_or_create_user_settings(
            session=session,
            user_id=user.id,
        )

        settings.show_fiber = show_fiber
        await session.commit()

    await callback.answer(
        (
            "✅ Настройка сохранена"
            if language == "ru"
            else "✅ Setting saved"
        )
    )

    if callback.message:
        if language == "ru":
            status_text = (
                "включено"
                if show_fiber
                else "выключено"
            )

            text = (
                "🌾 <b>Клетчатка</b>\n\n"
                f"Текущее состояние: "
                f"<b>{status_text}</b>\n\n"
                "Выберите, показывать ли клетчатку "
                "в продуктах, дневнике и блюдах."
            )
        else:
            status_text = (
                "enabled"
                if show_fiber
                else "disabled"
            )

            text = (
                "🌾 <b>Fiber</b>\n\n"
                f"Current status: "
                f"<b>{status_text}</b>\n\n"
                "Choose whether fiber should be shown "
                "in products, diary entries, and dishes."
            )

        await callback.message.edit_text(
            text,
            reply_markup=get_settings_fiber_keyboard(
                show_fiber=show_fiber,
                language=language,
            ),
        )

@router.callback_query(
    F.data == "settings_fiber:back"
)
async def back_from_fiber_settings(
    callback: CallbackQuery,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            (
                "⚙️ <b>Настройки</b>\n\n"
                "Выберите нужный раздел:"
                if language == "ru"
                else (
                    "⚙️ <b>Settings</b>\n\n"
                    "Choose a section:"
                )
            ),
            reply_markup=get_settings_keyboard(language),
        )

@router.message(
    F.text.in_(
        {
            "⚖️ Единицы измерения",
            "⚖️ Units",
        }
    )
)
async def units_settings_placeholder(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    text = (
        "⚖️ <b>Единицы измерения</b>\n\n"
        "Эта настройка пока недоступна."
        if language == "ru"
        else (
            "⚖️ <b>Units</b>\n\n"
            "This setting is not available yet."
        )
    )

    await message.answer(
        text,
        reply_markup=get_settings_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "🔔 Уведомления",
            "🔔 Notifications",
        }
    )
)
async def notifications_settings_placeholder(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    text = (
        "🔔 <b>Уведомления</b>\n\n"
        "Уведомления будут добавлены позже."
        if language == "ru"
        else (
            "🔔 <b>Notifications</b>\n\n"
            "Notifications will be added later."
        )
    )

    await message.answer(
        text,
        reply_markup=get_settings_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "👤 Профиль",
            "👤 Profile",
        }
    )
)
async def profile_settings_placeholder(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    text = (
        "👤 <b>Профиль</b>\n\n"
        "Раздел профиля будет добавлен позже."
        if language == "ru"
        else (
            "👤 <b>Profile</b>\n\n"
            "The profile section will be added later."
        )
    )

    await message.answer(
        text,
        reply_markup=get_settings_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "⬅️ Главное меню",
            "⬅️ Main menu",
        }
    )
)
async def back_to_main_menu_from_settings(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()

    await message.answer(
        get_text("main_menu", language),
        reply_markup=get_main_keyboard(language),
    )