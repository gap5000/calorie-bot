from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise


async def get_user_exercises(
    session: AsyncSession,
    user_id: int,
) -> list[Exercise]:
    result = await session.execute(
        select(Exercise)
        .where(
            Exercise.user_id == user_id
        )
        .order_by(
            Exercise.name
        )
    )

    return list(result.scalars().all())


async def create_exercise(
    session: AsyncSession,
    user_id: int,
    name: str,
) -> Exercise:
    exercise = Exercise(
        user_id=user_id,
        name=name,
    )

    session.add(exercise)

    await session.flush()

    return exercise


async def delete_exercise(
    session: AsyncSession,
    exercise: Exercise,
) -> None:
    await session.delete(exercise)