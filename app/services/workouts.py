from datetime import datetime
from typing import TypedDict
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.models.workout_set import WorkoutSet


class WorkoutSetData(TypedDict):
    exercise_id: int | None
    exercise_name: str
    set_number: int
    weight: float
    repetitions: int


async def save_workout(
    session: AsyncSession,
    user_id: int,
    sets: list[WorkoutSetData],
) -> Workout:
    workout = Workout(
        user_id=user_id,
    )

    session.add(workout)
    await session.flush()

    workout_sets = [
        WorkoutSet(
            workout_id=workout.id,
            exercise_id=item["exercise_id"],
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
from datetime import datetime

from sqlalchemy import select

from app.models.workout_set import WorkoutSet


class WorkoutDiaryEntry(TypedDict):
    exercise_name: str
    weight: float
    repetitions: int
    created_at: datetime


async def get_user_workout_diary(
    session: AsyncSession,
    user_id: int,
    limit: int = 100,
) -> list[WorkoutDiaryEntry]:
    result = await session.execute(
        select(
            WorkoutSet.exercise_name,
            WorkoutSet.weight,
            WorkoutSet.repetitions,
            Workout.created_at,
        )
        .join(
            Workout,
            Workout.id == WorkoutSet.workout_id,
        )
        .where(
            Workout.user_id == user_id
        )
        .order_by(
            Workout.created_at.desc()
        )
        .limit(limit)
    )

    rows = result.all()

    return [
        {
            "exercise_name": exercise_name,
            "weight": weight,
            "repetitions": repetitions,
            "created_at": created_at,
        }
        for (
            exercise_name,
            weight,
            repetitions,
            created_at,
        ) in rows
    ]