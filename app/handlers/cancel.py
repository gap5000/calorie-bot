from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main import get_main_keyboard
from app.services.users import get_user_language
from aiogram import F, Router

router = Router(name=__name__)


@router.message(Command("cancel"))

async def cancel_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    current_state = await state.get_state()
    language = await get_user_language(message.from_user.id)

    if current_state is None:
        if language == "ru":
            text = "Сейчас нет активного действия для отмены."
        else:
            text = "There is no active action to cancel."

        await message.answer(
            text,
            reply_markup=get_main_keyboard(language),
        )
        return

    await state.clear()

    if language == "ru":
        text = (
            "❌ Действие отменено.\n\n"
            "Вы вернулись в главное меню."
        )
    else:
        text = (
            "❌ Action cancelled.\n\n"
            "You have returned to the main menu."
        )

    await message.answer(
        text,
        reply_markup=get_main_keyboard(language),
    )