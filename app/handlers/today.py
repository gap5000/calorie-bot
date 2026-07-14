from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import func, select

from app.database.session import session_factory
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.models.user_settings import UserSettings
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "📊 Сегодня",
            "📊 Today",
        }
    )
)
async def today_handler(message: Message) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(message.from_user.id)

    now = datetime.now(timezone.utc)
    day_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )
        user = user_result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "User account was not found. Send /start."
            )
            return

        settings_result = await session.execute(
            select(UserSettings).where(
                UserSettings.user_id == user.id
            )
        )
        settings = settings_result.scalar_one_or_none()

        if (
            settings is None
            or settings.daily_calories is None
            or settings.daily_protein is None
            or settings.daily_fat is None
            or settings.daily_carbs is None
        ):
            await message.answer(
                get_text("nutrition_goal_missing", language)
            )
            return

        totals_result = await session.execute(
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
                NutritionEntry.user_id == user.id,
                NutritionEntry.created_at >= day_start,
            )
        )

        calories, protein, fat, carbs = totals_result.one()

    calories_left = max(
        settings.daily_calories - int(calories),
        0,
    )
    protein_left = max(
        settings.daily_protein - float(protein),
        0,
    )
    fat_left = max(
        settings.daily_fat - float(fat),
        0,
    )
    carbs_left = max(
        settings.daily_carbs - float(carbs),
        0,
    )

    if language == "ru":
        text = (
            "📊 <b>Сегодня</b>\n\n"
            "<b>Съедено:</b>\n"
            f"🔥 {int(calories)} / "
            f"{settings.daily_calories} ккал\n"
            f"🥩 {format_number(float(protein))} / "
            f"{format_number(settings.daily_protein)} г\n"
            f"🥑 {format_number(float(fat))} / "
            f"{format_number(settings.daily_fat)} г\n"
            f"🍚 {format_number(float(carbs))} / "
            f"{format_number(settings.daily_carbs)} г\n\n"
            "<b>Осталось:</b>\n"
            f"🔥 {calories_left} ккал\n"
            f"🥩 {format_number(protein_left)} г\n"
            f"🥑 {format_number(fat_left)} г\n"
            f"🍚 {format_number(carbs_left)} г"
        )
    else:
        text = (
            "📊 <b>Today</b>\n\n"
            "<b>Consumed:</b>\n"
            f"🔥 {int(calories)} / "
            f"{settings.daily_calories} kcal\n"
            f"🥩 {format_number(float(protein))} / "
            f"{format_number(settings.daily_protein)} g\n"
            f"🥑 {format_number(float(fat))} / "
            f"{format_number(settings.daily_fat)} g\n"
            f"🍚 {format_number(float(carbs))} / "
            f"{format_number(settings.daily_carbs)} g\n\n"
            "<b>Remaining:</b>\n"
            f"🔥 {calories_left} kcal\n"
            f"🥩 {format_number(protein_left)} g\n"
            f"🥑 {format_number(fat_left)} g\n"
            f"🍚 {format_number(carbs_left)} g"
        )

    await message.answer(text)


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))

    return f"{value:.1f}"