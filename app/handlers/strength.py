from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.main import get_main_keyboard
from app.keyboards.strength import get_strength_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

from sqlalchemy import select

from app.database.session import session_factory
from app.models.user import User
from app.services.workouts import (
    get_user_load_progressions,
    get_user_personal_records,
    get_user_workout_diary,
    delete_workout_diary_entry,
)
from app.keyboards.workout_diary import (
    get_delete_workout_entries_keyboard,
    get_workout_diary_keyboard,
)

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "💪 Силовые",
            "💪 Strength training",
        }
    )
)
async def strength_menu_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    if language == "ru":
        text = (
            "💪 <b>Силовые тренировки</b>\n\n"
            "Здесь можно вести дневник упражнений, "
            "следить за прогрессией нагрузки "
            "и смотреть личные рекорды."
        )
    else:
        text = (
            "💪 <b>Strength training</b>\n\n"
            "Here you can keep an exercise diary, "
            "track load progression "
            "and view personal records."
        )

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "📓 Дневник тренировок",
            "📓 Workout diary",
        }
    )
)
async def workout_diary_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
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

        entries = await get_user_workout_diary(
            session=session,
            user_id=user.id,
            limit=100,
        )

    if not entries:
        text = (
            "📓 <b>Дневник тренировок</b>\n\n"
            "Записей пока нет."
            if language == "ru"
            else (
                "📓 <b>Workout diary</b>\n\n"
                "There are no entries yet."
            )
        )

        await message.answer(
            text,
            reply_markup=get_workout_diary_keyboard(
                entries=entries,
                language=language,
    ),
)
        return

    lines = [
        (
            "📓 <b>Дневник тренировок</b>"
            if language == "ru"
            else "📓 <b>Workout diary</b>"
        ),
        "",
    ]

    current_date = None

    for entry in entries:
        created_at = entry["created_at"]
        date_text = created_at.strftime("%d.%m.%Y")

        if date_text != current_date:
            if current_date is not None:
                lines.append("")

            lines.append(f"<b>{date_text}</b>")
            current_date = date_text

        weight = format_number(entry["weight"])
        repetitions = entry["repetitions"]
        exercise_name = entry["exercise_name"]

        unit = "кг" if language == "ru" else "kg"

        lines.append(
            f"• {exercise_name} — "
            f"{weight} {unit} × {repetitions}"
        )

    text = "\n".join(lines)

    await message.answer(
        text,
        reply_markup=get_workout_diary_keyboard(
            entries=entries,
            language=language,
    ),
)
@router.message(
    F.text.in_(
        {
            "📈 Прогрессия нагрузки",
            "📈 Load progression",
        }
    )
)
async def load_progression_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
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

        progressions = await get_user_load_progressions(
            session=session,
            user_id=user.id,
        )

    if not progressions:
        text = (
            "📈 <b>Прогрессия нагрузки</b>\n\n"
            "Пока недостаточно данных."
            if language == "ru"
            else (
                "📈 <b>Load progression</b>\n\n"
                "There is not enough data yet."
            )
        )

        await message.answer(
            text,
            reply_markup=get_strength_keyboard(language),
        )
        return

    lines = [
        (
            "📈 <b>Прогрессия нагрузки</b>"
            if language == "ru"
            else "📈 <b>Load progression</b>"
        ),
        "",
    ]

    for progression in progressions:
        exercise_name = progression["exercise_name"]

        first_weight = progression["first_weight"]
        first_repetitions = progression["first_repetitions"]

        last_weight = progression["last_weight"]
        last_repetitions = progression["last_repetitions"]

        weight_change = last_weight - first_weight
        repetitions_change = (
            last_repetitions - first_repetitions
        )

        weight_sign = "+" if weight_change > 0 else ""
        repetitions_sign = (
            "+"
            if repetitions_change > 0
            else ""
        )

        unit = "кг" if language == "ru" else "kg"

        lines.append(f"<b>{exercise_name}</b>")

        lines.append(
            f"{format_number(first_weight)} {unit} × "
            f"{first_repetitions} → "
            f"{format_number(last_weight)} {unit} × "
            f"{last_repetitions}"
        )

        if language == "ru":
            lines.append(
                f"Изменение: {weight_sign}"
                f"{format_number(weight_change)} кг, "
                f"{repetitions_sign}"
                f"{repetitions_change} повт."
            )
        else:
            lines.append(
                f"Change: {weight_sign}"
                f"{format_number(weight_change)} kg, "
                f"{repetitions_sign}"
                f"{repetitions_change} reps"
            )

        lines.append("")

    text = "\n".join(lines).rstrip()

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )

@router.message(
    F.text.in_(
        {
            "🏆 Личные рекорды",
            "🏆 Personal records",
        }
    )
)
async def personal_records_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
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

        records = await get_user_personal_records(
            session=session,
            user_id=user.id,
        )

    if not records:
        text = (
            "🏆 <b>Личные рекорды</b>\n\n"
            "Пока нет сохранённых результатов."
            if language == "ru"
            else (
                "🏆 <b>Personal records</b>\n\n"
                "There are no saved results yet."
            )
        )

        await message.answer(
            text,
            reply_markup=get_strength_keyboard(language),
        )
        return

    lines = [
        (
            "🏆 <b>Личные рекорды</b>"
            if language == "ru"
            else "🏆 <b>Personal records</b>"
        ),
        "",
    ]

    for record in records:
        exercise_name = record["exercise_name"]
        maximum_weight = record["maximum_weight"]
        maximum_weight_repetitions = (
            record["maximum_weight_repetitions"]
        )
        estimated_one_rep_max = (
            record["estimated_one_rep_max"]
        )

        lines.append(f"<b>{exercise_name}</b>")

        if language == "ru":
            lines.append(
                "Максимальный вес: "
                f"{format_number(maximum_weight)} кг × "
                f"{maximum_weight_repetitions}"
            )
            lines.append(
                "Расчётный 1ПМ: "
                f"{format_number(estimated_one_rep_max)} кг"
            )
        else:
            lines.append(
                "Maximum weight: "
                f"{format_number(maximum_weight)} kg × "
                f"{maximum_weight_repetitions}"
            )
            lines.append(
                "Estimated 1RM: "
                f"{format_number(estimated_one_rep_max)} kg"
            )

        lines.append("")

    text = "\n".join(lines).rstrip()

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )

@router.callback_query(
    F.data == "workout_diary:delete_menu"
)
async def show_workout_delete_menu(
    callback: CallbackQuery,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "User account was not found",
                show_alert=True,
            )
            return

        entries = await get_user_workout_diary(
            session=session,
            user_id=user.id,
            limit=100,
        )

    await callback.answer()

    if callback.message:
        text = (
            "🗑 <b>Удаление записи</b>\n\n"
            "Выберите результат:"
            if language == "ru"
            else (
                "🗑 <b>Delete entry</b>\n\n"
                "Choose a result:"
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_delete_workout_entries_keyboard(
                entries=entries,
                language=language,
            ),
        )

@router.callback_query(
    F.data.regexp(r"^workout_diary:delete:\d+$")
)
async def delete_workout_entry_handler(
    callback: CallbackQuery,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    language = await get_user_language(
        callback.from_user.id
    )

    try:
        workout_set_id = int(
            callback.data.split(":")[2]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Entry not found",
            show_alert=True,
        )
        return

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "User account was not found",
                show_alert=True,
            )
            return

        deleted = await delete_workout_diary_entry(
            session=session,
            user_id=user.id,
            workout_set_id=workout_set_id,
        )

        await session.commit()

        entries = await get_user_workout_diary(
            session=session,
            user_id=user.id,
            limit=100,
        )

    if not deleted:
        await callback.answer(
            (
                "Запись уже удалена"
                if language == "ru"
                else "Entry is already deleted"
            ),
            show_alert=True,
        )
        return

    await callback.answer(
        (
            "✅ Запись удалена"
            if language == "ru"
            else "✅ Entry deleted"
        ),
        show_alert=True,
    )

    if callback.message:
        if entries:
            text = (
                "🗑 <b>Удаление записи</b>\n\n"
                "Выберите следующий результат:"
                if language == "ru"
                else (
                    "🗑 <b>Delete entry</b>\n\n"
                    "Choose another result:"
                )
            )

            await callback.message.edit_text(
                text,
                reply_markup=get_delete_workout_entries_keyboard(
                    entries=entries,
                    language=language,
                ),
            )
        else:
            await callback.message.edit_text(
                build_workout_diary_text(
                    entries=[],
                    language=language,
                ),
                reply_markup=get_workout_diary_keyboard(
                    entries=[],
                    language=language,
                ),
            )

@router.callback_query(
    F.data == "workout_diary:list"
)
async def back_to_workout_diary(
    callback: CallbackQuery,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "User account was not found",
                show_alert=True,
            )
            return

        entries = await get_user_workout_diary(
            session=session,
            user_id=user.id,
            limit=100,
        )

    await callback.answer()

    if callback.message:
        await callback.message.edit_text(
            build_workout_diary_text(
                entries=entries,
                language=language,
            ),
            reply_markup=get_workout_diary_keyboard(
                entries=entries,
                language=language,
            ),
        )

@router.callback_query(
    F.data == "workout_diary:back"
)
async def back_from_workout_diary(
    callback: CallbackQuery,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await callback.answer()

    if callback.message:
        text = (
            "💪 <b>Силовые тренировки</b>\n\n"
            "Выберите раздел:"
            if language == "ru"
            else (
                "💪 <b>Strength training</b>\n\n"
                "Choose a section:"
            )
        )

        await callback.message.answer(
            text,
            reply_markup=get_strength_keyboard(language),
        )

@router.message(
    F.text.in_(
        {
            "⬅️ Главное меню",
            "⬅️ Main menu",
        }
    )
)
async def back_to_main_menu_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await message.answer(
        get_text("main_menu", language),
        reply_markup=get_main_keyboard(language),
    )

def build_workout_diary_text(
    entries,
    language: str,
) -> str:
    if not entries:
        return (
            "📓 <b>Дневник тренировок</b>\n\n"
            "Записей пока нет."
            if language == "ru"
            else (
                "📓 <b>Workout diary</b>\n\n"
                "There are no entries yet."
            )
        )

    lines = [
        (
            "📓 <b>Дневник тренировок</b>"
            if language == "ru"
            else "📓 <b>Workout diary</b>"
        ),
        "",
    ]

    current_date = None

    for entry in entries:
        date_text = entry["created_at"].strftime(
            "%d.%m.%Y"
        )

        if date_text != current_date:
            if current_date is not None:
                lines.append("")

            lines.append(f"<b>{date_text}</b>")
            current_date = date_text

        unit = "кг" if language == "ru" else "kg"

        lines.append(
            f"• {entry['exercise_name']} — "
            f"{format_number(entry['weight'])} "
            f"{unit} × {entry['repetitions']}"
        )

    return "\n".join(lines)

def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"