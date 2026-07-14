import asyncio
import os

from app.database.init_db import create_tables
from aiogram import Bot
from app.handlers.features import router as features_router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from app.handlers.workout import router as workout_router
from aiogram import Bot, Dispatcher
from app.handlers.start import router as start_router
from app.handlers.metabolism import router as metabolism_router
from app.handlers.nutrition_goal import (
    router as nutrition_goal_router,
)

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
dp.include_router(start_router)
dp.include_router(metabolism_router)
dp.include_router(features_router)
dp.include_router(nutrition_goal_router)
dp.include_router(workout_router)

async def main() -> None:
    await create_tables()
    bot_info = await bot.get_me()

    print(f"Бот @{bot_info.username} успешно запущен")
    print("Для остановки нажми Ctrl + C")

    await dp.start_polling(bot)


if __name__ == "__main__":
    with asyncio.Runner(
        loop_factory=asyncio.SelectorEventLoop
    ) as runner:
        runner.run(main())