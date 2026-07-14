from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.strength import get_strength_keyboard
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "💪 Силовые",
            "💪 Strength training",
        }
    )
)
async def strength_menu_handler(message: Message) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(message.from_user.id)

    if language == "ru":
        text = (
            "💪 <b>Силовые тренировки</b>\n\n"
            "Начните новую тренировку или посмотрите "
            "свои упражнения и результаты."
        )
    else:
        text = (
            "💪 <b>Strength training</b>\n\n"
            "Start a new workout or review your "
            "exercises and results."
        )

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )