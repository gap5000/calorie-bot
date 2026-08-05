from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.dish_ingredient_method import (
    get_dish_ingredient_method_keyboard,
)
from app.keyboards.dishes import (
    get_dish_actions_keyboard,
    get_dishes_keyboard,
    get_saved_dishes_keyboard,
)
from app.keyboards.dish_ingredients import (
    get_dish_ingredient_products_keyboard,
)
import aiohttp

from app.services.product_search import (
    search_and_cache_products,
)
from app.models.product import Product
from app.services.users import get_user_language

from sqlalchemy import select

from app.database.session import session_factory
from app.models.user import User
from app.services.dishes import (
    calculate_dish_nutrition,
    create_dish,
    get_user_dish,
    get_user_dishes,
)
from app.states.dish import DishForm

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🍲 Мои блюда",
            "🍲 My dishes",
        }
    )
)
async def dishes_menu_handler(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()

    text = (
        "🍲 <b>Мои блюда</b>\n\n"
        "Создавайте блюда из нескольких продуктов "
        "и автоматически рассчитывайте КБЖУ "
        if language == "ru"
        else (
            "🍲 <b>My dishes</b>\n\n"
            "Create dishes from several products "
            "and automatically calculate calories, "
            "macros."
        )
    )

    await message.answer(
        text,
        reply_markup=get_dishes_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "➕ Создать блюдо",
            "➕ Create dish",
        }
    )
)
async def start_dish_creation(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(DishForm.name)

    text = (
        "➕ <b>Создание блюда</b>\n\n"
        "Введите название блюда:"
        if language == "ru"
        else (
            "➕ <b>Create dish</b>\n\n"
            "Enter the dish name:"
        )
    )

    await message.answer(text)

@router.message(DishForm.name)
async def process_dish_name(
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

    if not 2 <= len(name) <= 150:
        text = (
            "Название должно содержать от 2 до 150 символов."
            if language == "ru"
            else (
                "The name must contain "
                "between 2 and 150 characters."
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

        dish = await create_dish(
            session=session,
            user_id=user.id,
            name=name,
        )

        await session.commit()

    await state.clear()

    text = (
        "✅ <b>Блюдо создано</b>\n\n"
        f"🍲 {dish.name}\n\n"
        "Теперь нужно добавить ингредиенты."
        if language == "ru"
        else (
            "✅ <b>Dish created</b>\n\n"
            f"🍲 {dish.name}\n\n"
            "Now add ingredients."
        )
    )

    await message.answer(
        text,
        reply_markup=get_dishes_keyboard(language),
    )

@router.callback_query(
    F.data == "dish:add_ingredient"
)
async def show_dish_ingredient_methods(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()

    language = data.get(
        "language",
        await get_user_language(callback.from_user.id),
    )

    dish_id = data.get("selected_dish_id")

    if dish_id is None:
        await callback.answer(
            (
                "Сначала выберите блюдо"
                if language == "ru"
                else "Choose a dish first"
            ),
            show_alert=True,
        )
        return

    await callback.answer()

    text = (
        "➕ <b>Добавить ингредиент</b>\n\n"
        "Выберите способ добавления:"
        if language == "ru"
        else (
            "➕ <b>Add ingredient</b>\n\n"
            "Choose how to add the ingredient:"
        )
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_dish_ingredient_method_keyboard(
                language
            ),
        )

@router.callback_query(
    F.data == "dish_ingredient:search"
)
async def start_dish_ingredient_search(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get(
        "language",
        await get_user_language(callback.from_user.id),
    )

    await state.set_state(DishForm.ingredient_search)
    await callback.answer()

    if callback.message:
        text = (
            "🔎 <b>Поиск ингредиента</b>\n\n"
            "Введите название продукта:"
            if language == "ru"
            else (
                "🔎 <b>Ingredient search</b>\n\n"
                "Enter the product name:"
            )
        )

        await callback.message.answer(text)

@router.message(DishForm.ingredient_search)
async def search_dish_ingredient(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    query = " ".join(
        (message.text or "").strip().split()
    )

    if len(query) < 2:
        await message.answer(
            (
                "Введите минимум 2 символа."
                if language == "ru"
                else "Enter at least 2 characters."
            )
        )
        return

    searching_message = await message.answer(
        (
            "🔎 Ищу продукты..."
            if language == "ru"
            else "🔎 Searching for products..."
        )
    )

    try:
        async with session_factory() as session:
            products = await search_and_cache_products(
                session=session,
                query=query,
                limit=10,
            )

    except aiohttp.ClientResponseError as error:
        print(
            "Open Food Facts response error:",
            error.status,
            repr(error),
        )

        if error.status == 429:
            text = (
                "⏳ Выполнено слишком много запросов.\n\n"
                "Подождите немного и повторите поиск."
                if language == "ru"
                else (
                    "⏳ Too many requests were made.\n\n"
                    "Please wait and try again."
                )
            )
        elif error.status == 503:
            text = (
                "⚠️ Внешняя база продуктов временно "
                "недоступна.\n\n"
                "Попробуйте повторить поиск позже."
                if language == "ru"
                else (
                    "⚠️ The external product database "
                    "is temporarily unavailable.\n\n"
                    "Please try again later."
                )
            )
        else:
            text = (
                "⚠️ Не удалось выполнить внешний поиск."
                if language == "ru"
                else "⚠️ External search failed."
            )

        await searching_message.edit_text(text)
        return

    except (
        aiohttp.ClientError,
        TimeoutError,
    ) as error:
        print(
            "Open Food Facts connection error:",
            type(error).__name__,
            repr(error),
        )

        await searching_message.edit_text(
            (
                "⚠️ Не удалось подключиться "
                "к базе продуктов."
                if language == "ru"
                else (
                    "⚠️ Could not connect "
                    "to the product database."
                )
            )
        )
        return

    if not products:
        await searching_message.edit_text(
            (
                "Продукты не найдены.\n\n"
                "Попробуйте другое название."
                if language == "ru"
                else (
                    "No products were found.\n\n"
                    "Try another name."
                )
            )
        )
        return

    await searching_message.edit_text(
        (
            "🥗 <b>Выберите продукт:</b>"
            if language == "ru"
            else "🥗 <b>Choose a product:</b>"
        ),
        reply_markup=get_dish_ingredient_products_keyboard(
            products=products,
            language=language,
        ),
    )

@router.callback_query(
    F.data.regexp(r"^dish:select:\d+$")
)
async def select_dish_handler(
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
        dish_id = int(
            callback.data.split(":")[2]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Dish not found",
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

        dish = await get_user_dish(
            session=session,
            user_id=user.id,
            dish_id=dish_id,
        )

        if dish is None:
            await callback.answer(
                (
                    "Блюдо не найдено"
                    if language == "ru"
                    else "Dish not found"
                ),
                show_alert=True,
            )
            return

        nutrition = calculate_dish_nutrition(dish)

    await state.clear()
    await state.update_data(
        language=language,
        selected_dish_id=dish.id,
        selected_dish_name=dish.name,
    )

    await callback.answer()

    text = build_dish_card_text(
        dish=dish,
        nutrition=nutrition,
        language=language,
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_dish_actions_keyboard(
                language
            ),
        )

@router.callback_query(
    F.data == "dish:list"
)
async def back_to_saved_dishes(
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

        dishes = await get_user_dishes(
            session=session,
            user_id=user.id,
        )

    await callback.answer()

    text = (
        "📖 <b>Сохранённые блюда</b>\n\n"
        "Выберите блюдо:"
        if language == "ru"
        else (
            "📖 <b>Saved dishes</b>\n\n"
            "Choose a dish:"
        )
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_saved_dishes_keyboard(
                dishes=dishes,
                language=language,
            ),
        )

@router.callback_query(
    F.data == "dish:back_to_menu"
)
async def back_to_dishes_menu(
    callback: CallbackQuery,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await callback.answer()

    if callback.message:
        text = (
            "🍲 <b>Мои блюда</b>\n\n"
            "Выберите действие:"
            if language == "ru"
            else (
                "🍲 <b>My dishes</b>\n\n"
                "Choose an action:"
            )
        )

        await callback.message.answer(
            text,
            reply_markup=get_dishes_keyboard(language),
        )

@router.message(
    F.text.in_(
        {
            "📖 Сохранённые блюда",
            "📖 Saved dishes",
        }
    )
)
async def saved_dishes_handler(
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

        dishes = await get_user_dishes(
            session=session,
            user_id=user.id,
        )

    if not dishes:
        text = (
            "📖 <b>Сохранённые блюда</b>\n\n"
            "Список пока пуст."
            if language == "ru"
            else (
                "📖 <b>Saved dishes</b>\n\n"
                "The list is empty."
            )
        )

        await message.answer(
            text,
            reply_markup=get_saved_dishes_keyboard(
                dishes=dishes,
                language=language,
            ),
        )
        return

    text = (
    "📖 <b>Сохранённые блюда</b>\n\n"
    "Выберите блюдо:"
    if language == "ru"
    else (
        "📖 <b>Saved dishes</b>\n\n"
        "Choose a dish:"
    )
)

    await message.answer(
    text,
    reply_markup=get_saved_dishes_keyboard(
        dishes=dishes,
        language=language,
    ),
)

def build_dish_card_text(
    dish,
    nutrition,
    language: str,
) -> str:
    if language == "ru":
        lines = [
            f"🍲 <b>{dish.name}</b>",
            "",
            f"⚖️ Общий вес: "
            f"<b>{format_number(nutrition['total_grams'])} г</b>",
            "",
            "<b>На всё блюдо:</b>",
            f"🔥 {format_number(nutrition['calories'])} ккал",
            f"🥩 Белки: "
            f"{format_number(nutrition['protein'])} г",
            f"🥑 Жиры: "
            f"{format_number(nutrition['fat'])} г",
            f"🍚 Углеводы: "
            f"{format_number(nutrition['carbs'])} г",
            f"🌾 Клетчатка: "
            f"{format_number(nutrition['fiber'])} г",
            "",
            "<b>На 100 г:</b>",
            f"🔥 {format_number(nutrition['calories_100g'])} ккал",
            f"🥩 Белки: "
            f"{format_number(nutrition['protein_100g'])} г",
            f"🥑 Жиры: "
            f"{format_number(nutrition['fat_100g'])} г",
            f"🍚 Углеводы: "
            f"{format_number(nutrition['carbs_100g'])} г",
            f"🌾 Клетчатка: "
            f"{format_number(nutrition['fiber_100g'])} г",
        ]
    else:
        lines = [
            f"🍲 <b>{dish.name}</b>",
            "",
            f"⚖️ Total weight: "
            f"<b>{format_number(nutrition['total_grams'])} g</b>",
            "",
            "<b>Whole dish:</b>",
            f"🔥 {format_number(nutrition['calories'])} kcal",
            f"🥩 Protein: "
            f"{format_number(nutrition['protein'])} g",
            f"🥑 Fat: "
            f"{format_number(nutrition['fat'])} g",
            f"🍚 Carbs: "
            f"{format_number(nutrition['carbs'])} g",
            f"🌾 Fiber: "
            f"{format_number(nutrition['fiber'])} g",
            "",
            "<b>Per 100 g:</b>",
            f"🔥 {format_number(nutrition['calories_100g'])} kcal",
            f"🥩 Protein: "
            f"{format_number(nutrition['protein_100g'])} g",
            f"🥑 Fat: "
            f"{format_number(nutrition['fat_100g'])} g",
            f"🍚 Carbs: "
            f"{format_number(nutrition['carbs_100g'])} g",
            f"🌾 Fiber: "
            f"{format_number(nutrition['fiber_100g'])} g",
        ]

    if not dish.ingredients:
        lines.extend(
            [
                "",
                (
                    "Ингредиентов пока нет."
                    if language == "ru"
                    else "There are no ingredients yet."
                ),
            ]
        )

    return "\n".join(lines)


def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"