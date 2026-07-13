from aiogram import F, Router
from aiogram.types import Message

from app.locales.texts import get_text
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "ℹ️ Возможности бота",
            "ℹ️ Bot features",
        }
    )
)
async def features_handler(message: Message) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(message.from_user.id)

    await message.answer(
        get_text("features_text", language)
    )