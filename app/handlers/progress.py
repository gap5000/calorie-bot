from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.progress import get_progress_keyboard
from app.locales.texts import get_text
from app.models.user import User
from app.models.user_settings import UserSettings
from app.services.nutrition_stats import (
    get_nutrition_totals,
    get_period_days,
)
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "📊 Прогресс",
            "📊 Progress",
        }
    )
)
async def progress_menu_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await message.answer(
        get_text("progress_menu", language),
        reply_markup=get_progress_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "📅 Сегодня",
            "📅 Today",
            "🗓 Эта неделя",
            "🗓 This week",
            "📆 Этот месяц",
            "📆 This month",
        }
    )
)
async def progress_period_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    period_by_text = {
        "📅 Сегодня": "day",
        "📅 Today": "day",
        "🗓 Эта неделя": "week",
        "🗓 This week": "week",
        "📆 Этот месяц": "month",
        "📆 This month": "month",
    }

    period = period_by_text[message.text]
    days = get_period_days(period)

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )
        user = user_result.scalar_one_or_none()

        if user is None:
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

        if (
            settings.goal_expires_at is not None
            and settings.goal_expires_at
            <= datetime.now(timezone.utc)
        ):
            await message.answer(
                get_text("goal_expired", language)
            )
            return

        totals = await get_nutrition_totals(
            session=session,
            user_id=user.id,
            period=period,
        )

    calorie_goal = settings.daily_calories * days
    protein_goal = settings.daily_protein * days
    fat_goal = settings.daily_fat * days
    carbs_goal = settings.daily_carbs * days

    calories_left = max(
        calorie_goal - totals.calories,
        0,
    )
    protein_left = max(
        protein_goal - totals.protein,
        0,
    )
    fat_left = max(
        fat_goal - totals.fat,
        0,
    )
    carbs_left = max(
        carbs_goal - totals.carbs,
        0,
    )

    if language == "ru":
        period_names = {
            "day": "Сегодня",
            "week": "Текущая неделя",
            "month": "Текущий месяц",
        }

        text = (
            f"📊 <b>{period_names[period]}</b>\n\n"
            "<b>Употреблено:</b>\n"
            f"🔥 {totals.calories} / {calorie_goal} ккал\n"
            f"🥩 {format_number(totals.protein)} / "
            f"{format_number(protein_goal)} г\n"
            f"🥑 {format_number(totals.fat)} / "
            f"{format_number(fat_goal)} г\n"
            f"🍚 {format_number(totals.carbs)} / "
            f"{format_number(carbs_goal)} г\n\n"
            "<b>Осталось:</b>\n"
            f"🔥 {calories_left} ккал\n"
            f"🥩 {format_number(protein_left)} г\n"
            f"🥑 {format_number(fat_left)} г\n"
            f"🍚 {format_number(carbs_left)} г"
        )
    else:
        period_names = {
            "day": "Today",
            "week": "Current week",
            "month": "Current month",
        }

        text = (
            f"📊 <b>{period_names[period]}</b>\n\n"
            "<b>Consumed:</b>\n"
            f"🔥 {totals.calories} / {calorie_goal} kcal\n"
            f"🥩 {format_number(totals.protein)} / "
            f"{format_number(protein_goal)} g\n"
            f"🥑 {format_number(totals.fat)} / "
            f"{format_number(fat_goal)} g\n"
            f"🍚 {format_number(totals.carbs)} / "
            f"{format_number(carbs_goal)} g\n\n"
            "<b>Remaining:</b>\n"
            f"🔥 {calories_left} kcal\n"
            f"🥩 {format_number(protein_left)} g\n"
            f"🥑 {format_number(fat_left)} g\n"
            f"🍚 {format_number(carbs_left)} g"
        )

    await message.answer(text)


def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"