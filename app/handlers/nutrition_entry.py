from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User

from app.services.users import get_user_language
from app.states.nutrition_entry import NutritionEntryForm
from app.services.nutrition import calculate_calories_from_macros
from app.keyboards.nutrition import get_nutrition_keyboard
from app.keyboards.nutrition_entry import (
    get_back_keyboard,
    get_entry_finished_keyboard,
)
from app.services.favorite_products import add_favorite_product
from app.services.products import create_or_update_product

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
    get_text("nutrition_entry_intro", language),
    reply_markup=get_back_keyboard(language),
)

@router.message(
    F.text.in_(
        {
            "⬅️ Назад",
            "⬅️ Back",
        }
    )
)
async def back_to_nutrition_menu(
    message: Message,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()

    text = (
        "🍽 Вы вернулись в раздел питания."
        if language == "ru"
        else "🍽 You returned to nutrition."
    )

    await message.answer(
        text,
        reply_markup=get_nutrition_keyboard(language),
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
    await state.set_state(NutritionEntryForm.amount)

    if language == "ru":
        text = (
            "⚖️ Введите вес продукта в граммах.\n\n"
            "Например: 250"
        )
    else:
        text = (
            "⚖️ Enter the product weight in grams.\n\n"
            "Example: 250"
        )

    await message.answer(text)

@router.message(NutritionEntryForm.amount)
async def process_amount(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        amount = float(
            (message.text or "").replace(",", ".")
        )
    except ValueError:
        amount = None

    if amount is None or not 1 <= amount <= 10000:
        if language == "ru":
            text = (
                "Введите вес от 1 до 10000 граммов."
            )
        else:
            text = (
                "Enter a weight from 1 to 10000 grams."
            )

        await message.answer(text)
        return

    await state.update_data(amount=amount)
    await state.set_state(
        NutritionEntryForm.calories
    )

    await message.answer(
        get_text(
            "nutrition_enter_calories",
            language,
        )
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

    if carbs is None:
        await message.answer(
            get_text(
                "nutrition_invalid_macro",
                language,
            )
        )
        return

    amount = float(data["amount"])
    calories = int(data["calories"])
    protein = float(data["protein"])
    fat = float(data["fat"])

    calculated_calories = calculate_calories_from_macros(
        protein=protein,
        fat=fat,
        carbs=carbs,
    )

    multiplier = 100 / amount

    calories_100g = round(
        calories * multiplier,
        1,
    )
    protein_100g = round(
        protein * multiplier,
        1,
    )
    fat_100g = round(
        fat * multiplier,
        1,
    )
    carbs_100g = round(
        carbs * multiplier,
        1,
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
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
        )

        session.add(entry)

        product = await create_or_update_product(
            session=session,
            name=data["name"],
            brand=None,
            barcode=None,
            calories_100g=calories_100g,
            protein_100g=protein_100g,
            fat_100g=fat_100g,
            carbs_100g=carbs_100g,
            source="manual",
        )

        await session.commit()

        product_id = product.id

    await state.clear()
    await state.update_data(
        language=language,
        last_manual_product_id=product_id,
    )

    result_text = get_text(
        "nutrition_entry_saved",
        language,
    ).format(
        name=data["name"],
        calories=calories,
        calculated_calories=calculated_calories,
        protein=format_number(protein),
        fat=format_number(fat),
        carbs=format_number(carbs),
    )

    await message.answer(
        result_text,
        reply_markup=get_entry_finished_keyboard(
            language
        ),
    )

@router.callback_query(
    F.data == "manual:add_favorite"
)
async def add_manual_product_to_favorites(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")
    product_id = data.get(
        "last_manual_product_id"
    )

    if product_id is None:
        await callback.answer(
            "Product not found",
            show_alert=True,
        )
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "User account was not found",
                show_alert=True,
            )
            return

        _, created = await add_favorite_product(
            session=session,
            user_id=user.id,
            product_id=product_id,
        )

        await session.commit()

    text = (
        "⭐ Продукт добавлен в избранное"
        if created and language == "ru"
        else (
            "⭐ Этот продукт уже есть в избранном"
            if language == "ru"
            else (
                "⭐ Product added to favorites"
                if created
                else "⭐ Product is already in favorites"
            )
        )
    )

    await callback.answer(
        text,
        show_alert=True,
    )

@router.callback_query(
    F.data == "manual:add_again"
)
async def add_another_manual_product(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(
        NutritionEntryForm.name
    )
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text(
                "nutrition_entry_intro",
                language,
            ),
            reply_markup=get_back_keyboard(language),
        )

@router.callback_query(
    F.data == "manual:finish"
)
async def finish_manual_entry(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await callback.answer()

    if callback.message:
        text = (
            "✅ Добавление питания завершено."
            if language == "ru"
            else "✅ Nutrition entry completed."
        )

        await callback.message.answer(
            text,
            reply_markup=get_nutrition_keyboard(
                language
            ),
        )

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