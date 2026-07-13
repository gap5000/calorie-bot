from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import F
from aiogram.types import CallbackQuery, Message

from app.keyboards.language import language_keyboard
from app.locales.texts import get_text

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        get_text("choose_language", "ru"),
        reply_markup=language_keyboard,
    )

@router.callback_query(F.data.startswith("language:"))
async def language_handler(callback: CallbackQuery) -> None:
    language = callback.data.split(":")[1]

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("welcome", language)
        )