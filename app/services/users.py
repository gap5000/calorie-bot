from sqlalchemy import select

from app.database.session import session_factory
from app.models.user import User


async def get_user_language(telegram_id: int) -> str:
    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

    if user is None or user.language not in {"ru", "en"}:
        return "en"

    return user.language