from app.database.connection import engine
from app.models.base import Base
from app.models.user import User
from app.models.user_settings import UserSettings


async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)