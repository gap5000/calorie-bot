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

    language = await get_user_language(message.from_user.id)

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(NutritionGoalForm.calories)

    await message.answer(
        get_text("goal_intro", language)
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

    await message.answer(
        get_text("enter_fat_goal", language)
    )


@router.message(NutritionGoalForm.fat)
async def process_fat(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    fat = parse_macro_value(message.text)

    if fat is None:
        await message.answer(
            get_text("invalid_macro_goal", language)
        )
        return

    await state.update_data(fat=fat)
    await state.set_state(NutritionGoalForm.carbs)

    await message.answer(
        get_text("enter_carbs_goal", language)
    )


@router.message(NutritionGoalForm.carbs)
async def process_carbs(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")

    carbs = parse_macro_value(message.text)

    if carbs is None:
        await message.answer(
            get_text("invalid_macro_goal", language)
        )
        return

    calories = data["calories"]
    protein = data["protein"]
    fat = data["fat"]

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await state.clear()

            await message.answer(
                "User account was not found. Send /start."
            )
            return

        await update_nutrition_goal(
            session=session,
            user_id=user.id,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
        )

        await session.commit()

    await state.clear()

    result_text = get_text("goal_saved", language).format(
        calories=calories,
        protein=format_number(protein),
        fat=format_number(fat),
        carbs=format_number(carbs),
    )

    await message.answer(result_text)


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