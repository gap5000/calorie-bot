from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings
from datetime import datetime


async def get_or_create_user_settings(
    session: AsyncSession,
    user_id: int,
) -> UserSettings:
    result = await session.execute(
        select(UserSettings).where(
            UserSettings.user_id == user_id
        )
    )

    settings = result.scalar_one_or_none()

    if settings is not None:
        return settings

    settings = UserSettings(user_id=user_id)
    session.add(settings)

    await session.flush()

    return settings

async def update_nutrition_goal(
    session: AsyncSession,
    user_id: int,
    calories: int,
    protein: float,
    fat: float,
    carbs: float,
    goal_period: str,
    goal_started_at: datetime,
    goal_expires_at: datetime | None,
) -> UserSettings:
    settings = await get_or_create_user_settings(
        session=session,
        user_id=user_id,
    )

    settings.daily_calories = calories
    settings.daily_protein = protein
    settings.daily_fat = fat
    settings.daily_carbs = carbs

    settings.goal_period = goal_period
    settings.goal_started_at = goal_started_at
    settings.goal_expires_at = goal_expires_at

    await session.flush()

    return settings