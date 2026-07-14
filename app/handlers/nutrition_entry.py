from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.database.session import session_factory
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.services.users import get_user_language
from app.states.nutrition_entry import NutritionEntryForm
from app.services.nutrition import calculate_calories_from_macros

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "➕ Добавить питание",
            "➕ Add nutrition",
        }
    )
)
async def start_nutrition_entry(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(message.from_user.id)

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(NutritionEntryForm.name)

    await message.answer(
        get_text("nutrition_entry_intro", language)
    )


@router.message(NutritionEntryForm.name)
async def process_name(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    name = (message.text or "").strip()

    if not 2 <= len(name) <= 100:
        await message.answer(
            get_text("nutrition_invalid_name", language)
        )
        return

    await state.update_data(name=name)
    await state.set_state(NutritionEntryForm.calories)

    await message.answer(
        get_text("nutrition_enter_calories", language)
    )


@router.message(NutritionEntryForm.calories)
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
            get_text("nutrition_invalid_calories", language)
        )
        return

    if not 0 <= calories <= 10_000:
        await message.answer(
            get_text("nutrition_invalid_calories", language)
        )
        return

    await state.update_data(calories=calories)
    await state.set_state(NutritionEntryForm.protein)

    await message.answer(
        get_text("nutrition_enter_protein", language)
    )


@router.message(NutritionEntryForm.protein)
async def process_protein(
    message: Message,
    state: FSMContext,
) -> None:
    await process_macro(
        message=message,
        state=state,
        field_name="protein",
        next_state=NutritionEntryForm.fat,
        next_text_key="nutrition_enter_fat",
    )


@router.message(NutritionEntryForm.fat)
async def process_fat(
    message: Message,
    state: FSMContext,
) -> None:
    await process_macro(
        message=message,
        state=state,
        field_name="fat",
        next_state=NutritionEntryForm.carbs,
        next_text_key="nutrition_enter_carbs",
    )


@router.message(NutritionEntryForm.carbs)
async def process_carbs(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")

    carbs = parse_macro(message.text)
    calculated_calories = calculate_calories_from_macros(
        protein=data["protein"],
        fat=data["fat"],
        carbs=carbs,
    )

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

        entry = NutritionEntry(
            user_id=user.id,
            name=data["name"],
            calories=data["calories"],
            protein=data["protein"],
            fat=data["fat"],
            carbs=carbs,
        )

        session.add(entry)
        await session.commit()

    await state.clear()

    result_text = get_text(
        "nutrition_entry_saved",
        language,
    ).format(
        name=data["name"],
        calories=data["calories"],
        calculated_calories=calculated_calories,
        protein=format_number(data["protein"]),
        fat=format_number(data["fat"]),
        carbs=format_number(carbs),
    )

    await message.answer(result_text)


async def process_macro(
    message: Message,
    state: FSMContext,
    field_name: str,
    next_state,
    next_text_key: str,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    value = parse_macro(message.text)

    if value is None:
        await message.answer(
            get_text("nutrition_invalid_macro", language)
        )
        return

    await state.update_data(**{field_name: value})
    await state.set_state(next_state)

    await message.answer(
        get_text(next_text_key, language)
    )


def parse_macro(value: str | None) -> float | None:
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