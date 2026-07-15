import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nutrition_entry import NutritionEntry


@dataclass(slots=True)
class NutritionTotals:
    calories: int
    protein: float
    fat: float
    carbs: float


def get_period_start(
    period: str,
) -> datetime:
    now = datetime.now(timezone.utc)

    if period == "day":
        return now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "week":
        day_start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        return day_start - timedelta(
            days=now.weekday()
        )

    if period == "month":
        return now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    raise ValueError("Unsupported period")


def get_period_days(period: str) -> int:
    now = datetime.now(timezone.utc)

    if period == "day":
        return 1

    if period == "week":
        return 7

    if period == "month":
        return calendar.monthrange(
            now.year,
            now.month,
        )[1]

    raise ValueError("Unsupported period")


async def get_nutrition_totals(
    session: AsyncSession,
    user_id: int,
    period: str,
) -> NutritionTotals:
    period_start = get_period_start(period)

    result = await session.execute(
        select(
            func.coalesce(
                func.sum(NutritionEntry.calories),
                0,
            ),
            func.coalesce(
                func.sum(NutritionEntry.protein),
                0,
            ),
            func.coalesce(
                func.sum(NutritionEntry.fat),
                0,
            ),
            func.coalesce(
                func.sum(NutritionEntry.carbs),
                0,
            ),
        ).where(
            NutritionEntry.user_id == user_id,
            NutritionEntry.created_at >= period_start,
        )
    )

    calories, protein, fat, carbs = result.one()

    return NutritionTotals(
        calories=int(calories),
        protein=float(protein),
        fat=float(fat),
        carbs=float(carbs),
    )