from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from app.models.workout_set import WorkoutSet
from app.models.workout import Workout

from app.services.workouts import (
    WorkoutSetData,
    save_workout,
)
from app.database.session import session_factory
from app.keyboards.exercises import (
    get_delete_exercises_keyboard,
    get_exercise_actions_keyboard,
    get_exercises_keyboard,
)
from app.keyboards.strength import get_strength_keyboard
from app.models.exercise import Exercise
from app.models.user import User
from app.services.exercises import (
    create_exercise,
    delete_exercise,
    get_user_exercises,
)
from app.services.users import get_user_language
from app.states.exercise import ExerciseForm

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🏋️ Мои упражнения",
            "🏋️ My exercises",
        }
    )
)
async def show_exercises(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()

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

        exercises = await get_user_exercises(
            session=session,
            user_id=user.id,
        )

    text = get_exercises_list_text(
        exercises=exercises,
        language=language,
    )

    await message.answer(
        text,
        reply_markup=get_exercises_keyboard(
            exercises=exercises,
            language=language,
        ),
    )


@router.callback_query(
    F.data == "exercise:add"
)
async def request_exercise_name(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(ExerciseForm.name)

    await callback.answer()

    if callback.message:
        text = (
            "➕ <b>Новое упражнение</b>\n\n"
            "Введите название упражнения:"
            if language == "ru"
            else (
                "➕ <b>New exercise</b>\n\n"
                "Enter the exercise name:"
            )
        )

        await callback.message.answer(text)


@router.message(ExerciseForm.name)
async def process_exercise_name(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")

    name = " ".join(
        (message.text or "").strip().split()
    )

    if not 2 <= len(name) <= 100:
        text = (
            "Название должно содержать от 2 до 100 символов."
            if language == "ru"
            else (
                "The name must contain "
                "between 2 and 100 characters."
            )
        )

        await message.answer(text)
        return

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await state.clear()

            await message.answer(
                "User account was not found. Send /start."
            )
            return

        duplicate_result = await session.execute(
            select(Exercise).where(
                Exercise.user_id == user.id,
                Exercise.name.ilike(name),
            )
        )

        existing_exercise = (
            duplicate_result.scalar_one_or_none()
        )

        if existing_exercise is not None:
            text = (
                "⚠️ Такое упражнение уже есть в вашем списке."
                if language == "ru"
                else (
                    "⚠️ This exercise is already "
                    "in your list."
                )
            )

            await message.answer(text)
            return

        exercise = await create_exercise(
            session=session,
            user_id=user.id,
            name=name,
        )

        await session.commit()

    await state.clear()

    text = (
        "✅ <b>Упражнение добавлено</b>\n\n"
        f"🏋️ {exercise.name}"
        if language == "ru"
        else (
            "✅ <b>Exercise added</b>\n\n"
            f"🏋️ {exercise.name}"
        )
    )

    await message.answer(
        text,
        reply_markup=get_exercise_actions_keyboard(
            language
        ),
    )

    await state.update_data(
        language=language,
        selected_exercise_id=exercise.id,
        selected_exercise_name=exercise.name,
    )


@router.callback_query(
    F.data.regexp(r"^exercise:select:\d+$")
)
async def select_exercise(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    language = await get_user_language(
        callback.from_user.id
    )

    try:
        exercise_id = int(
            callback.data.split(":")[2]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Exercise not found",
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

        exercise_result = await session.execute(
            select(Exercise).where(
                Exercise.id == exercise_id,
                Exercise.user_id == user.id,
            )
        )

        exercise = exercise_result.scalar_one_or_none()

        if exercise is None:
            await callback.answer(
                (
                    "Упражнение не найдено"
                    if language == "ru"
                    else "Exercise not found"
                ),
                show_alert=True,
            )
            return

    await state.clear()
    await state.update_data(
        language=language,
        selected_exercise_id=exercise.id,
        selected_exercise_name=exercise.name,
    )

    await callback.answer()

    if callback.message:
        text = (
            f"🏋️ <b>{exercise.name}</b>\n\n"
            "Выберите действие:"
            if language == "ru"
            else (
                f"🏋️ <b>{exercise.name}</b>\n\n"
                "Choose an action:"
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_exercise_actions_keyboard(
                language
            ),
        )


@router.callback_query(
    F.data == "exercise:delete_menu"
)
async def show_delete_exercises_menu(
    callback: CallbackQuery,
    state: FSMContext,
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

        exercises = await get_user_exercises(
            session=session,
            user_id=user.id,
        )

    await callback.answer()

    if callback.message:
        text = (
            "🗑 <b>Удаление упражнения</b>\n\n"
            "Выберите упражнение:"
            if language == "ru"
            else (
                "🗑 <b>Delete exercise</b>\n\n"
                "Choose an exercise:"
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_delete_exercises_keyboard(
                exercises=exercises,
                language=language,
            ),
        )


@router.callback_query(
    F.data.regexp(r"^exercise:delete:\d+$")
)
async def remove_exercise(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    language = await get_user_language(
        callback.from_user.id
    )

    try:
        exercise_id = int(
            callback.data.split(":")[2]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Exercise not found",
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

        exercise_result = await session.execute(
            select(Exercise).where(
                Exercise.id == exercise_id,
                Exercise.user_id == user.id,
            )
        )

        exercise = exercise_result.scalar_one_or_none()

        if exercise is None:
            await callback.answer(
                (
                    "Упражнение уже удалено"
                    if language == "ru"
                    else "Exercise is already deleted"
                ),
                show_alert=True,
            )
            return

        exercise_name = exercise.name

        await delete_exercise(
            session=session,
            exercise=exercise,
        )

        await session.commit()

        exercises = await get_user_exercises(
            session=session,
            user_id=user.id,
        )

    await callback.answer(
        (
            f"✅ {exercise_name} удалено"
            if language == "ru"
            else f"✅ {exercise_name} deleted"
        ),
        show_alert=True,
    )

    if callback.message:
        if exercises:
            text = (
                "🗑 <b>Удаление упражнения</b>\n\n"
                "Выберите следующее упражнение:"
                if language == "ru"
                else (
                    "🗑 <b>Delete exercise</b>\n\n"
                    "Choose another exercise:"
                )
            )

            await callback.message.edit_text(
                text,
                reply_markup=get_delete_exercises_keyboard(
                    exercises=exercises,
                    language=language,
                ),
            )
        else:
            await callback.message.edit_text(
                get_exercises_list_text(
                    exercises=[],
                    language=language,
                ),
                reply_markup=get_exercises_keyboard(
                    exercises=[],
                    language=language,
                ),
            )


@router.callback_query(
    F.data == "exercise:list"
)
async def back_to_exercises_list(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()

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

        exercises = await get_user_exercises(
            session=session,
            user_id=user.id,
        )

    await callback.answer()

    if callback.message:
        await callback.message.edit_text(
            get_exercises_list_text(
                exercises=exercises,
                language=language,
            ),
            reply_markup=get_exercises_keyboard(
                exercises=exercises,
                language=language,
            ),
        )


@router.callback_query(
    F.data == "exercise:back"
)
async def back_to_strength_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await callback.answer()

    text = (
        "💪 <b>Силовые тренировки</b>\n\n"
        "Выберите раздел:"
        if language == "ru"
        else (
            "💪 <b>Strength training</b>\n\n"
            "Choose a section:"
        )
    )

    if callback.message:
        await callback.message.answer(
            text,
            reply_markup=get_strength_keyboard(language),
        )

@router.callback_query(
    F.data == "exercise:add_result"
)
async def request_result_weight(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")

    if exercise_id is None or exercise_name is None:
        await callback.answer(
            (
                "Сначала выберите упражнение"
                if language == "ru"
                else "Choose an exercise first"
            ),
            show_alert=True,
        )
        return

    await state.set_state(
        ExerciseForm.result_weight
    )
    await callback.answer()

    if callback.message:
        text = (
            f"🏋️ <b>{exercise_name}</b>\n\n"
            "Введите рабочий вес в килограммах:"
            if language == "ru"
            else (
                f"🏋️ <b>{exercise_name}</b>\n\n"
                "Enter the working weight in kilograms:"
            )
        )

        await callback.message.answer(text)

@router.message(ExerciseForm.result_weight)
async def process_result_weight(
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
        weight = None

    if weight is None or not 0 <= weight <= 1000:
        text = (
            "Введите корректный вес от 0 до 1000 кг."
            if language == "ru"
            else (
                "Enter a valid weight "
                "from 0 to 1000 kg."
            )
        )

        await message.answer(text)
        return

    await state.update_data(
        result_weight=weight
    )
    await state.set_state(
        ExerciseForm.result_repetitions
    )

    text = (
        "🔢 Введите количество повторений:"
        if language == "ru"
        else "🔢 Enter the number of repetitions:"
    )

    await message.answer(text)

@router.message(ExerciseForm.result_repetitions)
async def process_result_repetitions(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")

    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")
    weight = data.get("result_weight")

    if (
        exercise_id is None
        or exercise_name is None
        or weight is None
    ):
        await state.clear()

        await message.answer(
            (
                "Не удалось найти выбранное упражнение."
                if language == "ru"
                else "The selected exercise was not found."
            )
        )
        return

    try:
        repetitions = int(message.text or "")
    except ValueError:
        repetitions = None

    if (
        repetitions is None
        or not 1 <= repetitions <= 1000
    ):
        text = (
            "Введите число повторений от 1 до 1000."
            if language == "ru"
            else (
                "Enter a repetition count "
                "from 1 to 1000."
            )
        )

        await message.answer(text)
        return

    workout_set: WorkoutSetData = {
        "exercise_id": exercise_id,
        "exercise_name": exercise_name,
        "set_number": 1,
        "weight": float(weight),
        "repetitions": repetitions,
    }

    async with session_factory() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await state.clear()

            await message.answer(
                "User account was not found. Send /start."
            )
            return

        await save_workout(
            session=session,
            user_id=user.id,
            sets=[workout_set],
        )

        await session.commit()

    await state.clear()
    await state.update_data(
        language=language,
        selected_exercise_id=exercise_id,
        selected_exercise_name=exercise_name,
    )

    if language == "ru":
        text = (
            "✅ <b>Результат сохранён</b>\n\n"
            f"🏋️ {exercise_name}\n"
            f"⚖️ {format_number(float(weight))} кг\n"
            f"🔢 {repetitions} повторений"
        )
    else:
        text = (
            "✅ <b>Result saved</b>\n\n"
            f"🏋️ {exercise_name}\n"
            f"⚖️ {format_number(float(weight))} kg\n"
            f"🔢 {repetitions} repetitions"
        )

    await message.answer(
        text,
        reply_markup=get_exercise_actions_keyboard(
            language
        ),
    )

@router.callback_query(
    F.data == "exercise:history"
)
async def show_exercise_history(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")

    if exercise_id is None or exercise_name is None:
        await callback.answer(
            (
                "Сначала выберите упражнение"
                if language == "ru"
                else "Choose an exercise first"
            ),
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

        history_result = await session.execute(
            select(
                WorkoutSet,
                Workout.created_at,
            )
            .join(
                Workout,
                Workout.id == WorkoutSet.workout_id,
            )
            .where(
                Workout.user_id == user.id,
                WorkoutSet.exercise_id == exercise_id,
            )
            .order_by(
                Workout.created_at.desc()
            )
            .limit(20)
        )

        history = history_result.all()

    await callback.answer()

    if not history:
        text = (
            f"📓 <b>{exercise_name}</b>\n\n"
            "История пока пуста."
            if language == "ru"
            else (
                f"📓 <b>{exercise_name}</b>\n\n"
                "The history is empty."
            )
        )
    else:
        lines = [
            f"📓 <b>{exercise_name}</b>",
            "",
        ]

        for workout_set, created_at in history:
            date_text = created_at.strftime(
                "%d.%m.%Y"
            )

            if language == "ru":
                result_line = (
                    f"• {date_text} — "
                    f"{format_number(workout_set.weight)} кг × "
                    f"{workout_set.repetitions}"
                )
            else:
                result_line = (
                    f"• {date_text} — "
                    f"{format_number(workout_set.weight)} kg × "
                    f"{workout_set.repetitions}"
                )

            lines.append(result_line)

        text = "\n".join(lines)

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_exercise_actions_keyboard(
                language
            ),
        )

@router.callback_query(
    F.data == "exercise:progression"
)
async def show_exercise_progression(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")

    if exercise_id is None or exercise_name is None:
        await callback.answer(
            (
                "Сначала выберите упражнение"
                if language == "ru"
                else "Choose an exercise first"
            ),
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

        history_result = await session.execute(
            select(
                WorkoutSet,
                Workout.created_at,
            )
            .join(
                Workout,
                Workout.id == WorkoutSet.workout_id,
            )
            .where(
                Workout.user_id == user.id,
                WorkoutSet.exercise_id == exercise_id,
            )
            .order_by(
                Workout.created_at.asc()
            )
            .limit(100)
        )

        history = history_result.all()

    await callback.answer()

    if not history:
        text = (
            f"📈 <b>{exercise_name}</b>\n\n"
            "Пока недостаточно данных для прогрессии."
            if language == "ru"
            else (
                f"📈 <b>{exercise_name}</b>\n\n"
                "There is not enough data yet."
            )
        )

    elif len(history) == 1:
        workout_set, created_at = history[0]

        date_text = created_at.strftime("%d.%m.%Y")

        if language == "ru":
            text = (
                f"📈 <b>{exercise_name}</b>\n\n"
                "Пока есть только один результат:\n\n"
                f"• {date_text} — "
                f"{format_number(workout_set.weight)} кг × "
                f"{workout_set.repetitions}\n\n"
                "Добавьте ещё один результат, "
                "чтобы увидеть прогрессию."
            )
        else:
            text = (
                f"📈 <b>{exercise_name}</b>\n\n"
                "There is only one result so far:\n\n"
                f"• {date_text} — "
                f"{format_number(workout_set.weight)} kg × "
                f"{workout_set.repetitions}\n\n"
                "Add another result to see progression."
            )

    else:
        first_set, first_date = history[0]
        last_set, last_date = history[-1]

        weight_change = (
            last_set.weight - first_set.weight
        )
        repetitions_change = (
            last_set.repetitions
            - first_set.repetitions
        )

        first_date_text = first_date.strftime("%d.%m.%Y")
        last_date_text = last_date.strftime("%d.%m.%Y")

        weight_sign = "+" if weight_change > 0 else ""
        repetitions_sign = (
            "+"
            if repetitions_change > 0
            else ""
        )

        if language == "ru":
            text = (
                f"📈 <b>{exercise_name}</b>\n\n"
                "<b>Первый результат:</b>\n"
                f"• {first_date_text} — "
                f"{format_number(first_set.weight)} кг × "
                f"{first_set.repetitions}\n\n"
                "<b>Последний результат:</b>\n"
                f"• {last_date_text} — "
                f"{format_number(last_set.weight)} кг × "
                f"{last_set.repetitions}\n\n"
                "<b>Изменение:</b>\n"
                f"⚖️ Вес: {weight_sign}"
                f"{format_number(weight_change)} кг\n"
                f"🔢 Повторения: {repetitions_sign}"
                f"{repetitions_change}"
            )
        else:
            text = (
                f"📈 <b>{exercise_name}</b>\n\n"
                "<b>First result:</b>\n"
                f"• {first_date_text} — "
                f"{format_number(first_set.weight)} kg × "
                f"{first_set.repetitions}\n\n"
                "<b>Latest result:</b>\n"
                f"• {last_date_text} — "
                f"{format_number(last_set.weight)} kg × "
                f"{last_set.repetitions}\n\n"
                "<b>Change:</b>\n"
                f"⚖️ Weight: {weight_sign}"
                f"{format_number(weight_change)} kg\n"
                f"🔢 Repetitions: {repetitions_sign}"
                f"{repetitions_change}"
            )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_exercise_actions_keyboard(
                language
            ),
        )

@router.callback_query(
    F.data == "exercise:record"
)
async def show_exercise_record(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")

    if exercise_id is None or exercise_name is None:
        await callback.answer(
            (
                "Сначала выберите упражнение"
                if language == "ru"
                else "Choose an exercise first"
            ),
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

        results_query = await session.execute(
            select(
                WorkoutSet,
                Workout.created_at,
            )
            .join(
                Workout,
                Workout.id == WorkoutSet.workout_id,
            )
            .where(
                Workout.user_id == user.id,
                WorkoutSet.exercise_id == exercise_id,
            )
            .order_by(
                Workout.created_at.desc()
            )
        )

        results = results_query.all()

    await callback.answer()

    if not results:
        text = (
            f"🏆 <b>{exercise_name}</b>\n\n"
            "Результатов пока нет."
            if language == "ru"
            else (
                f"🏆 <b>{exercise_name}</b>\n\n"
                "There are no results yet."
            )
        )
    else:
        max_weight_set, max_weight_date = max(
            results,
            key=lambda item: (
                item[0].weight,
                item[0].repetitions,
            ),
        )

        best_estimated_set, best_estimated_date = max(
            results,
            key=lambda item: calculate_estimated_one_rep_max(
                weight=item[0].weight,
                repetitions=item[0].repetitions,
            ),
        )

        estimated_one_rep_max = (
            calculate_estimated_one_rep_max(
                weight=best_estimated_set.weight,
                repetitions=best_estimated_set.repetitions,
            )
        )

        max_weight_date_text = (
            max_weight_date.strftime("%d.%m.%Y")
        )
        estimated_date_text = (
            best_estimated_date.strftime("%d.%m.%Y")
        )

        if language == "ru":
            text = (
                f"🏆 <b>{exercise_name}</b>\n\n"
                "<b>Максимальный вес:</b>\n"
                f"⚖️ {format_number(max_weight_set.weight)} кг × "
                f"{max_weight_set.repetitions}\n"
                f"📅 {max_weight_date_text}\n\n"
                "<b>Лучший расчётный 1ПМ:</b>\n"
                f"🏆 {format_number(estimated_one_rep_max)} кг\n"
                f"На основе результата: "
                f"{format_number(best_estimated_set.weight)} кг × "
                f"{best_estimated_set.repetitions}\n"
                f"📅 {estimated_date_text}"
            )
        else:
            text = (
                f"🏆 <b>{exercise_name}</b>\n\n"
                "<b>Maximum weight:</b>\n"
                f"⚖️ {format_number(max_weight_set.weight)} kg × "
                f"{max_weight_set.repetitions}\n"
                f"📅 {max_weight_date_text}\n\n"
                "<b>Best estimated 1RM:</b>\n"
                f"🏆 {format_number(estimated_one_rep_max)} kg\n"
                f"Based on: "
                f"{format_number(best_estimated_set.weight)} kg × "
                f"{best_estimated_set.repetitions}\n"
                f"📅 {estimated_date_text}"
            )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_exercise_actions_keyboard(
                language
            ),
        )

def get_exercises_list_text(
    exercises: list[Exercise],
    language: str,
) -> str:
    if not exercises:
        return (
            "🏋️ <b>Мои упражнения</b>\n\n"
            "Список пока пуст.\n\n"
            "Добавьте первое упражнение."
            if language == "ru"
            else (
                "🏋️ <b>My exercises</b>\n\n"
                "The list is empty.\n\n"
                "Add your first exercise."
            )
        )

    return (
        "🏋️ <b>Мои упражнения</b>\n\n"
        "Выберите упражнение:"
        if language == "ru"
        else (
            "🏋️ <b>My exercises</b>\n\n"
            "Choose an exercise:"
        )
    )
def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"

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