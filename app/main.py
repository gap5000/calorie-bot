import asyncio
import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не найдена в файле .env")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "<b>Привет!</b>\n\n"
        "Я помогу тебе считать калории, белки, жиры и углеводы."
    )

async def main() -> None:
    bot_info = await bot.get_me()

    print(f"Бот @{bot_info.username} успешно запущен")
    print("Для остановки нажми Ctrl + C")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())