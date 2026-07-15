from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main import get_main_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "⬅️ Главное меню",
            "⬅️ Main menu",
        }
    )
)
async def back_to_main_menu(
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