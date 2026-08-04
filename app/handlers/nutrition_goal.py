from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.database.session import session_factory
from app.locales.texts import get_text
from app.models.user import User
from app.services.user_settings import update_nutrition_goal
from app.services.users import get_user_language
from app.states.nutrition_goal import NutritionGoalForm
from app.services.nutrition import calculate_calories_from_macros
from datetime import datetime, timedelta, timezone

from aiogram.types import CallbackQuery, Message

from app.keyboards.main import get_main_keyboard
from app.keyboards.metabolism import gender_keyboard
from app.services.user_settings import (
    get_or_create_user_settings,
    update_nutrition_goal,
)
from app.states.metabolism import MetabolismForm

from app.keyboards.nutrition_goal import (
    get_goal_actions_keyboard,
    get_goal_period_keyboard,
)

from app.keyboards.nutrition_goal import (
    get_goal_period_keyboard,
)
from app.keyboards.navigation import (
    get_back_to_main_keyboard,
)

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🎯 Настроить цель КБЖУ",
            "🎯 Set calorie and macro goals",
        }
    )
)
async def start_goal_setup(
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

        settings = await get_or_create_user_settings(
            session=session,
            user_id=user.id,
        )

        await session.commit()

    goal_is_configured = all(
        value is not None
        for value in (
            settings.daily_calories,
            settings.daily_protein,
            settings.daily_fat,
            settings.daily_carbs,
        )
    )

    if goal_is_configured:
        period_text = get_text(
            f"goal_period_{settings.goal_period}",
            language,
        )

        if language == "ru":
            text = (
                "🎯 <b>Дневная цель КБЖУ</b>\n\n"
                "<b>Текущие значения:</b>\n\n"
                f"🔥 Калории: "
                f"<b>{settings.daily_calories} ккал</b>\n"
                f"🥩 Белки: "
                f"<b>{format_number(settings.daily_protein)} г</b>\n"
                f"🥑 Жиры: "
                f"<b>{format_number(settings.daily_fat)} г</b>\n"
                f"🍚 Углеводы: "
                f"<b>{format_number(settings.daily_carbs)} г</b>\n\n"
                f"📅 Период: <b>{period_text}</b>\n\n"
                "Выберите действие:"
            )
        else:
            text = (
                "🎯 <b>Daily calorie and macro goal</b>\n\n"
                "<b>Current values:</b>\n\n"
                f"🔥 Calories: "
                f"<b>{settings.daily_calories} kcal</b>\n"
                f"🥩 Protein: "
                f"<b>{format_number(settings.daily_protein)} g</b>\n"
                f"🥑 Fat: "
                f"<b>{format_number(settings.daily_fat)} g</b>\n"
                f"🍚 Carbs: "
                f"<b>{format_number(settings.daily_carbs)} g</b>\n\n"
                f"📅 Period: <b>{period_text}</b>\n\n"
                "Choose an action:"
            )
    else:
        text = (
            "🎯 <b>Дневная цель КБЖУ</b>\n\n"
            "Цель пока не настроена.\n\n"
            "Вы можете ввести значения вручную "
            "или сначала рассчитать примерную норму."
            if language == "ru"
            else (
                "🎯 <b>Daily calorie and macro goal</b>\n\n"
                "The goal has not been configured yet.\n\n"
                "You can enter the values manually "
                "or calculate an estimated daily need first."
            )
        )

    await message.answer(
        text,
        reply_markup=get_goal_actions_keyboard(language),
    )

@router.callback_query(
    F.data == "nutrition_goal:edit"
)
async def start_manual_goal_edit(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(NutritionGoalForm.calories)

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("goal_intro", language),
            reply_markup=get_back_to_main_keyboard(language),
        )

@router.callback_query(
    F.data == "nutrition_goal:calculate"
)
async def start_goal_calculation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(MetabolismForm.gender)

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("metabolism_intro", language),
            reply_markup=gender_keyboard,
        )

        await callback.message.answer(
            (
                "Вы можете вернуться в главное меню "
                "в любой момент."
                if language == "ru"
                else (
                    "You can return to the main menu "
                    "at any time."
                )
            ),
            reply_markup=get_back_to_main_keyboard(language),
        )

@router.callback_query(
    F.data == "nutrition_goal:back"
)
async def back_from_nutrition_goal(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("main_menu", language),
            reply_markup=get_main_keyboard(language),
        )

@router.message(NutritionGoalForm.calories)
async def process_calories(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        calories = int(message.text or "")
    except ValueError:
        await message.answer(
            get_text("invalid_calories_goal", language)
        )
        return

    if not 500 <= calories <= 10_000:
        await message.answer(
            get_text("invalid_calories_goal", language)
        )
        return

    await state.update_data(calories=calories)
    await state.set_state(NutritionGoalForm.protein)

    await message.answer(
        get_text("enter_protein_goal", language)
    )


@router.message(NutritionGoalForm.protein)
async def process_protein(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    protein = parse_macro_value(message.text)

    if protein is None:
        await message.answer(
            get_text("invalid_macro_goal", language)
        )
        return

    await state.update_data(protein=protein)
    await state.set_state(NutritionGoalForm.fat)

    calculated_calories = calculate_calories_from_macros(
        protein=protein,
        fat=0,
        carbs=0,
    )

    if language == "ru":
        progress_text = (
            "\n\n🧮 Сейчас по БЖУ: "
            f"<b>{calculated_calories} ккал</b>"
        )
    else:
        progress_text = (
            "\n\n🧮 Current calories from macros: "
            f"<b>{calculated_calories} kcal</b>"
        )

    await message.answer(
        get_text("enter_fat_goal", language)
        + progress_text
    )


@router.message(NutritionGoalForm.fat)
async def process_fat(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")
    protein = data["protein"]

    fat = parse_macro_value(message.text)

    if fat is None:
        await message.answer(
            get_text("invalid_macro_goal", language)
        )
        return

    await state.update_data(fat=fat)
    await state.set_state(NutritionGoalForm.carbs)

    calculated_calories = calculate_calories_from_macros(
        protein=protein,
        fat=fat,
        carbs=0,
    )

    if language == "ru":
        progress_text = (
            f"\n\n🧮 Сейчас по БЖУ: "
            f"<b>{calculated_calories} ккал</b>"
        )
    else:
        progress_text = (
            f"\n\n🧮 Current calories from macros: "
            f"<b>{calculated_calories} kcal</b>"
        )

    await message.answer(
        get_text("enter_carbs_goal", language)
        + progress_text
    )

@router.message(NutritionGoalForm.carbs)
async def process_carbs(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    carbs = parse_macro_value(message.text)

    if carbs is None:
        await message.answer(
            get_text("invalid_macro_goal", language)
        )
        return

    protein = data["protein"]
    fat = data["fat"]

    calculated_calories = calculate_calories_from_macros(
        protein=protein,
        fat=fat,
        carbs=carbs,
    )

    await state.update_data(
        carbs=carbs,
        calculated_calories=calculated_calories,
    )

    await state.set_state(NutritionGoalForm.period)

    await message.answer(
        get_text("choose_goal_period", language),
        reply_markup=get_goal_period_keyboard(language),
    )

    @router.callback_query(
        NutritionGoalForm.period,
        F.data.startswith("goal_period:"),
    )
    async def process_goal_period(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        if callback.data is None:
            await callback.answer()
            return

        period = callback.data.split(":")[1]

        allowed_periods = {
            "day",
            "week",
            "month",
            "unlimited",
        }

        if period not in allowed_periods:
            await callback.answer("Unsupported period")
            return

        data = await state.get_data()
        language = data.get("language", "en")

        started_at = datetime.now(timezone.utc)

        period_durations = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
        }

        duration = period_durations.get(period)

        expires_at = (
            started_at + duration
            if duration is not None
            else None
        )

        async with session_factory() as session:
            result = await session.execute(
                select(User).where(
                    User.telegram_id == callback.from_user.id
                )
            )

            user = result.scalar_one_or_none()

            if user is None:
                await state.clear()
                await callback.answer()

                if callback.message:
                    await callback.message.answer(
                        "User account was not found. Send /start."
                    )
                return

            await update_nutrition_goal(
                session=session,
                user_id=user.id,
                calories=data["calories"],
                protein=data["protein"],
                fat=data["fat"],
                carbs=data["carbs"],
                goal_period=period,
                goal_started_at=started_at,
                goal_expires_at=expires_at,
            )

            await session.commit()

        period_text = get_text(
            f"goal_period_{period}",
            language,
        )

        result_text = get_text(
            "goal_saved",
            language,
        ).format(
            calories=data["calories"],
            calculated_calories=data["calculated_calories"],
            protein=format_number(data["protein"]),
            fat=format_number(data["fat"]),
            carbs=format_number(data["carbs"]),
            period=period_text,
        )

        await state.clear()
        await callback.answer()

        if callback.message:
            await callback.message.answer(result_text)


def parse_macro_value(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        number = float(value.replace(",", "."))
    except ValueError:
        return None

    if not 0 <= number <= 1000:
        return None

    return number


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))

    return str(value)