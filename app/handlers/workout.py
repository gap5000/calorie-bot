from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.workout import get_workout_actions_keyboard
from app.locales.texts import get_text
from app.models.user import User
from app.services.users import get_user_language
from app.services.workouts import WorkoutSetData, save_workout
from app.states.workout import WorkoutForm

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🏋️ Силовая тренировка",
            "🏋️ Strength workout",
        }
    )
)
async def start_workout(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(message.from_user.id)

    await state.clear()
    await state.update_data(
        language=language,
        sets=[],
    )
    await state.set_state(WorkoutForm.exercise_name)

    await message.answer(
        get_text("workout_intro", language)
    )


@router.message(Command("cancel"))
async def cancel_workout(
    message: Message,
    state: FSMContext,
) -> None:
    current_state = await state.get_state()

    if current_state is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")

    await state.clear()

    await message.answer(
        get_text("workout_cancelled", language)
    )


@router.message(WorkoutForm.exercise_name)
async def process_exercise_name(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    exercise_name = (message.text or "").strip()

    if not 2 <= len(exercise_name) <= 100:
        await message.answer(
            get_text("workout_invalid_exercise", language)
        )
        return

    await state.update_data(
        current_exercise=exercise_name
    )
    await state.set_state(WorkoutForm.weight)

    await message.answer(
        get_text("workout_enter_weight", language)
    )


@router.message(WorkoutForm.weight)
async def process_weight(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        weight = float(
            (message.text or "").replace(",", ".")
        )
    except ValueError:
        await message.answer(
            get_text("workout_invalid_weight", language)
        )
        return

    if not 0 <= weight <= 1000:
        await message.answer(
            get_text("workout_invalid_weight", language)
        )
        return

    await state.update_data(current_weight=weight)
    await state.set_state(WorkoutForm.repetitions)

    await message.answer(
        get_text("workout_enter_repetitions", language)
    )


@router.message(WorkoutForm.repetitions)
async def process_repetitions(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        repetitions = int(message.text or "")
    except ValueError:
        await message.answer(
            get_text(
                "workout_invalid_repetitions",
                language,
            )
        )
        return

    if not 1 <= repetitions <= 1000:
        await message.answer(
            get_text(
                "workout_invalid_repetitions",
                language,
            )
        )
        return

    exercise_name = data["current_exercise"]
    weight = data["current_weight"]

    sets: list[WorkoutSetData] = data.get("sets", [])

    set_number = (
        sum(
            1
            for item in sets
            if item["exercise_name"] == exercise_name
        )
        + 1
    )

    new_set: WorkoutSetData = {
        "exercise_name": exercise_name,
        "set_number": set_number,
        "weight": weight,
        "repetitions": repetitions,
    }

    sets.append(new_set)

    await state.update_data(sets=sets)
    await state.set_state(WorkoutForm.next_action)

    await message.answer(
        get_text("workout_set_added", language).format(
            exercise=exercise_name,
            set_number=set_number,
            weight=format_number(weight),
            repetitions=repetitions,
        ),
        reply_markup=get_workout_actions_keyboard(language),
    )


@router.callback_query(
    WorkoutForm.next_action,
    F.data == "workout:same_exercise",
)
async def add_same_exercise_set(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    await state.set_state(WorkoutForm.weight)
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("workout_enter_weight", language)
        )


@router.callback_query(
    WorkoutForm.next_action,
    F.data == "workout:new_exercise",
)
async def add_new_exercise(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    await state.set_state(WorkoutForm.exercise_name)
    await callback.answer()

    if callback.message:
        if language == "ru":
            text = "Введите название следующего упражнения:"
        else:
            text = "Enter the name of the next exercise:"

        await callback.message.answer(text)


@router.callback_query(
    WorkoutForm.next_action,
    F.data == "workout:finish",
)
async def finish_workout(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    telegram_user = callback.from_user
    data = await state.get_data()

    language = data.get("language", "en")
    sets: list[WorkoutSetData] = data.get("sets", [])

    await callback.answer()

    if not sets:
        if callback.message:
            await callback.message.answer(
                get_text("workout_empty", language)
            )
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await state.clear()

            if callback.message:
                await callback.message.answer(
                    "User account was not found. Send /start."
                )
            return

        await save_workout(
            session=session,
            user_id=user.id,
            sets=sets,
        )

        await session.commit()

    summary = build_workout_summary(sets)
    await state.clear()

    if callback.message:
        await callback.message.answer(
            get_text("workout_saved", language).format(
                summary=summary,
                sets_count=len(sets),
            )
        )


def build_workout_summary(
    sets: list[WorkoutSetData],
) -> str:
    lines: list[str] = []
    previous_exercise: str | None = None

    for item in sets:
        exercise_name = item["exercise_name"]

        if exercise_name != previous_exercise:
            if lines:
                lines.append("")

            lines.append(f"<b>{exercise_name}</b>")
            previous_exercise = exercise_name

        lines.append(
            f"{item['set_number']}. "
            f"{format_number(item['weight'])} кг × "
            f"{item['repetitions']}"
        )

    return "\n".join(lines)


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))

    return str(value)