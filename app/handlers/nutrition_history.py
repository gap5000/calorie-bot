from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.nutrition_history import (
    get_nutrition_history_keyboard,
)
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "📋 История питания",
            "📋 Nutrition history",
        }
    )
)
async def nutrition_history_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

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

        entries_result = await session.execute(
            select(NutritionEntry)
            .where(
                NutritionEntry.user_id == user.id,
                NutritionEntry.created_at >= day_start,
            )
            .order_by(
                NutritionEntry.created_at.desc()
            )
        )

        entries = list(
            entries_result.scalars().all()
        )

    if not entries:
        await message.answer(
            get_text(
                "nutrition_history_empty",
                language,
            )
        )
        return

    await message.answer(
        get_text(
            "nutrition_history_title",
            language,
        ),
        reply_markup=get_nutrition_history_keyboard(
            entries=entries,
            language=language,
        ),
    )
@router.callback_query(
    F.data.startswith("nutrition_delete:")
)
async def delete_nutrition_entry(
    callback: CallbackQuery,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    language = await get_user_language(
        callback.from_user.id
    )

    try:
        entry_id = int(
            callback.data.split(":")[1]
        )
    except (ValueError, IndexError):
        await callback.answer()
        return

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )
        user = user_result.scalar_one_or_none()

        if user is None:
            await callback.answer()
            return

        entry_result = await session.execute(
            select(NutritionEntry).where(
                NutritionEntry.id == entry_id,
                NutritionEntry.user_id == user.id,
            )
        )

        entry = entry_result.scalar_one_or_none()

        if entry is None:
            await callback.answer(
                get_text(
                    "nutrition_entry_not_found",
                    language,
                ),
                show_alert=True,
            )
            return

        entry_name = entry.name or "Food"
        entry_calories = entry.calories

        await session.delete(entry)
        await session.commit()

        await callback.answer()

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await callback.message.answer(
            get_text(
                "nutrition_entry_deleted",
                language,
            ).format(
                name=entry_name,
                calories=entry_calories,
            )
        )