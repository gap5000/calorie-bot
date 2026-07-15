from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.nutrition import get_nutrition_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🍽 Питание",
            "🍽 Nutrition",
        }
    )
)
async def nutrition_menu_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await message.answer(
        get_text("nutrition_menu", language),
        reply_markup=get_nutrition_keyboard(language),
    )