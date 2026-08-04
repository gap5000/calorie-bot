from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.main import get_main_keyboard
from app.keyboards.strength import get_strength_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

from sqlalchemy import select

from app.database.session import session_factory
from app.models.user import User
from app.services.workouts import get_user_workout_diary
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
            reply_markup=get_strength_keyboard(language),
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
        reply_markup=get_strength_keyboard(language),
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

    if language == "ru":
        text = (
            "📈 <b>Прогрессия нагрузки</b>\n\n"
            "Здесь будет отображаться изменение "
            "веса, повторений и тренировочного объёма "
            "по каждому упражнению.\n\n"
            "Функцию подключим после дневника."
        )
    else:
        text = (
            "📈 <b>Load progression</b>\n\n"
            "Changes in weight, repetitions "
            "and training volume will be shown here.\n\n"
            "We will connect this after the diary."
        )

    await message.answer(
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

def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"