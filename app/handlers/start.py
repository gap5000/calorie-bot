from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.language import language_keyboard
from app.keyboards.main import get_main_keyboard
from app.locales.texts import get_text
from app.models.user import User

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    telegram_user = message.from_user

    if telegram_user is None:
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_user.id
            )
        )

        user = result.scalar_one_or_none()

    if user is None or user.language is None:
        await message.answer(
            "🌍 <b>Choose your language / Выберите язык</b>",
            reply_markup=language_keyboard,
        )
        return

    await message.answer(
        get_text("main_menu", user.language),
        reply_markup=get_main_keyboard(user.language),
    )


@router.callback_query(F.data.startswith("language:"))
async def language_handler(callback: CallbackQuery) -> None:
    telegram_user = callback.from_user
    callback_data = callback.data

    if callback_data is None:
        await callback.answer()
        return

    language = callback_data.split(":")[1]

    if language not in {"ru", "en"}:
        await callback.answer("Unsupported language")
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                language=language,
            )
            session.add(user)
        else:
            user.username = telegram_user.username
            user.first_name = telegram_user.first_name
            user.language = language

        await session.commit()

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("welcome", language),
            reply_markup=get_main_keyboard(language),
        )