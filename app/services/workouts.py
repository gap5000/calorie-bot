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


class WorkoutDiaryEntry(TypedDict):
    workout_set_id: int
    exercise_id: int | None
    exercise_name: str
    weight: float
    repetitions: int
    created_at: datetime


class ExerciseProgressionData(TypedDict):
    exercise_id: int
    exercise_name: str
    first_weight: float
    first_repetitions: int
    first_date: datetime
    last_weight: float
    last_repetitions: int
    last_date: datetime


class ExerciseRecordData(TypedDict):
    exercise_id: int
    exercise_name: str
    maximum_weight: float
    maximum_weight_repetitions: int
    estimated_one_rep_max: float

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


async def get_user_workout_diary(
    session: AsyncSession,
    user_id: int,
    limit: int = 100,
) -> list[WorkoutDiaryEntry]:
    result = await session.execute(
        select(
            WorkoutSet.id,
            WorkoutSet.exercise_id,
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
            "workout_set_id": workout_set_id,
            "exercise_id": exercise_id,
            "exercise_name": exercise_name,
            "weight": weight,
            "repetitions": repetitions,
            "created_at": created_at,
        }
        for (
            workout_set_id,
            exercise_id,
            exercise_name,
            weight,
            repetitions,
            created_at,
        ) in rows
    ]


async def get_user_load_progressions(
    session: AsyncSession,
    user_id: int,
) -> list[ExerciseProgressionData]:
    result = await session.execute(
        select(
            WorkoutSet.exercise_id,
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
            Workout.user_id == user_id,
            WorkoutSet.exercise_id.is_not(None),
        )
        .order_by(
            Workout.created_at.asc()
        )
    )

    rows = result.all()

    grouped_results: dict[
        int,
        list[tuple[str, float, int, datetime]],
    ] = {}

    for (
        exercise_id,
        exercise_name,
        weight,
        repetitions,
        created_at,
    ) in rows:
        if exercise_id is None:
            continue

        grouped_results.setdefault(
            exercise_id,
            [],
        ).append(
            (
                exercise_name,
                float(weight),
                repetitions,
                created_at,
            )
        )

    progressions: list[ExerciseProgressionData] = []

    for exercise_id, exercise_results in grouped_results.items():
        first_result = exercise_results[0]
        last_result = exercise_results[-1]

        progressions.append(
            {
                "exercise_id": exercise_id,
                "exercise_name": last_result[0],
                "first_weight": first_result[1],
                "first_repetitions": first_result[2],
                "first_date": first_result[3],
                "last_weight": last_result[1],
                "last_repetitions": last_result[2],
                "last_date": last_result[3],
            }
        )

    progressions.sort(
        key=lambda item: item["exercise_name"].lower()
    )

    return progressions

async def get_user_personal_records(
    session: AsyncSession,
    user_id: int,
) -> list[ExerciseRecordData]:
    result = await session.execute(
        select(
            WorkoutSet.exercise_id,
            WorkoutSet.exercise_name,
            WorkoutSet.weight,
            WorkoutSet.repetitions,
        )
        .join(
            Workout,
            Workout.id == WorkoutSet.workout_id,
        )
        .where(
            Workout.user_id == user_id,
            WorkoutSet.exercise_id.is_not(None),
        )
    )

    rows = result.all()

    grouped_results: dict[
        int,
        list[tuple[str, float, int]],
    ] = {}

    for (
        exercise_id,
        exercise_name,
        weight,
        repetitions,
    ) in rows:
        if exercise_id is None:
            continue

        grouped_results.setdefault(
            exercise_id,
            [],
        ).append(
            (
                exercise_name,
                float(weight),
                repetitions,
            )
        )

    records: list[ExerciseRecordData] = []

    for exercise_id, exercise_results in grouped_results.items():
        maximum_weight_result = max(
            exercise_results,
            key=lambda item: (
                item[1],
                item[2],
            ),
        )

        best_estimated_result = max(
            exercise_results,
            key=lambda item: calculate_estimated_one_rep_max(
                weight=item[1],
                repetitions=item[2],
            ),
        )

        records.append(
            {
                "exercise_id": exercise_id,
                "exercise_name": maximum_weight_result[0],
                "maximum_weight": maximum_weight_result[1],
                "maximum_weight_repetitions": (
                    maximum_weight_result[2]
                ),
                "estimated_one_rep_max": (
                    calculate_estimated_one_rep_max(
                        weight=best_estimated_result[1],
                        repetitions=best_estimated_result[2],
                    )
                ),
            }
        )

    records.sort(
        key=lambda item: item["exercise_name"].lower()
    )

    return records


def calculate_estimated_one_rep_max(
    weight: float,
    repetitions: int,
) -> float:
    if repetitions == 1:
        return float(weight)

    estimated = weight * (
        1 + repetitions / 30
    )

    return round(estimated, 1)

async def delete_workout_diary_entry(
    session: AsyncSession,
    user_id: int,
    workout_set_id: int,
) -> bool:
    result = await session.execute(
        select(WorkoutSet)
        .join(
            Workout,
            Workout.id == WorkoutSet.workout_id,
        )
        .where(
            WorkoutSet.id == workout_set_id,
            Workout.user_id == user_id,
        )
    )

    workout_set = result.scalar_one_or_none()

    if workout_set is None:
        return False

    workout_id = workout_set.workout_id

    await session.delete(workout_set)
    await session.flush()

    remaining_result = await session.execute(
        select(WorkoutSet.id)
        .where(
            WorkoutSet.workout_id == workout_id
        )
        .limit(1)
    )

    remaining_set_id = (
        remaining_result.scalar_one_or_none()
    )

    if remaining_set_id is None:
        workout_result = await session.execute(
            select(Workout).where(
                Workout.id == workout_id,
                Workout.user_id == user_id,
            )
        )

        workout = workout_result.scalar_one_or_none()

        if workout is not None:
            await session.delete(workout)

    return True