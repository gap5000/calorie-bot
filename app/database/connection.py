import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Переменная DATABASE_URL не найдена в файле .env")

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
)