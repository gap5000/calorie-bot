from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.keyboards.main import main_keyboard

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
         "<b>Привет!</b>\n\n"
        "Я помогу тебе считать калории, белки, жиры и углеводы.\n\n"
        "Для начала настрой дневную цель.",
        reply_markup=main_keyboard
    )
