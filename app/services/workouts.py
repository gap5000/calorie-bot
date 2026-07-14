from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.models.workout_set import WorkoutSet


class WorkoutSetData(TypedDict):
    exercise_name: str
    set_number: int
    weight: float
    repetitions: int


async def save_workout(
    session: AsyncSession,
    user_id: int,
    sets: list[WorkoutSetData],
) -> Workout:
    workout = Workout(user_id=user_id)

    session.add(workout)
    await session.flush()

    workout_sets = [
        WorkoutSet(
            workout_id=workout.id,
            exercise_name=item["exercise_name"],
            set_number=item["set_number"],
            weight=item["weight"],
            repetitions=item["repetitions"],
        )
        for item in sets
    ]

    session.add_all(workout_sets)
    await session.flush()

    return workout