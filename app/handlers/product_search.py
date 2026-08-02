import aiohttp

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from app.services.favorite_products import add_favorite_product

from app.database.session import session_factory
from app.keyboards.product_search import (
    get_product_results_keyboard,
    get_selected_product_keyboard,
)
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.services.open_food_facts import (
    search_products_by_name as search_external_products,
)
from app.services.products import (
    create_or_update_product,
    search_products_by_name as search_local_products,
)
from app.services.users import get_user_language
from app.states.product_search import ProductSearchForm

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🔎 Найти продукт",
            "🔎 Search product",
        }
    )
)
async def start_product_search(
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
    await state.set_state(ProductSearchForm.query)

    await message.answer(
        get_text("product_search_intro", language)
    )


@router.message(ProductSearchForm.query)
async def process_product_query(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    query = (message.text or "").strip()

    if not 2 <= len(query) <= 80:
        await message.answer(
            get_text(
                "product_search_invalid",
                language,
            )
        )
        return

    searching_message = await message.answer(
        get_text("product_searching", language)
    )

    # Сначала ищем продукт в собственной PostgreSQL.
    async with session_factory() as session:
        local_products = await search_local_products(
            session=session,
            query=query,
            limit=5,
        )

        if local_products:
            products = [
                product_to_dict(product)
                for product in local_products
            ]

            await show_search_results(
                searching_message=searching_message,
                state=state,
                products=products,
                language=language,
            )
            return

        # Если локально ничего нет — обращаемся
        # к Open Food Facts.
        try:
            external_products = await search_external_products(
                query=query,
                limit=5,
            )
        except aiohttp.ClientResponseError as error:
            print(
                "Open Food Facts response error:",
                error.status,
                repr(error),
            )

            error_text = get_external_error_text(
                status=error.status,
                language=language,
            )

            await searching_message.edit_text(error_text)
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
                get_text(
                    "barcode_service_error",
                    language,
                )
            )
            return

        if not external_products:
            await searching_message.edit_text(
                get_text(
                    "product_search_empty",
                    language,
                )
            )
            return

        # Сохраняем найденные внешние продукты
        # в нашу собственную базу.
        saved_products = []

        for external_product in external_products:
            saved_product = await create_or_update_product(
                session=session,
                name=external_product.name,
                brand=external_product.brand,
                barcode=external_product.barcode,
                calories_100g=external_product.calories_100g,
                protein_100g=external_product.protein_100g,
                fat_100g=external_product.fat_100g,
                carbs_100g=external_product.carbs_100g,
                source="open_food_facts",
            )

            saved_products.append(saved_product)

        await session.commit()

        products = [
            product_to_dict(product)
            for product in saved_products
        ]

    await show_search_results(
        searching_message=searching_message,
        state=state,
        products=products,
        language=language,
    )


async def show_search_results(
    searching_message: Message,
    state: FSMContext,
    products: list[dict],
    language: str,
) -> None:
    await state.update_data(products=products)
    await state.set_state(ProductSearchForm.selection)

    await searching_message.edit_text(
        get_text(
            "product_search_results",
            language,
        ),
        reply_markup=get_product_results_keyboard(
            products=products,
            language=language,
        ),
    )


@router.callback_query(
    ProductSearchForm.selection,
    F.data == "product_search:retry",
)
async def retry_product_search(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    await state.set_state(ProductSearchForm.query)
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text(
                "product_search_intro",
                language,
            )
        )


@router.callback_query(
    ProductSearchForm.selection,
    F.data.regexp(r"^product_search:\d+$"),
)
async def select_product(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    data = await state.get_data()
    language = data.get("language", "en")
    products = data.get("products", [])

    try:
        index = int(callback.data.split(":")[1])
        product = products[index]
    except (ValueError, IndexError, KeyError):
        await callback.answer(
            "Product not found",
            show_alert=True,
        )
        return

    await state.update_data(
        selected_product=product
    )

    brand_line = (
        f"🏷 {product['brand']}\n\n"
        if product.get("brand")
        else ""
    )

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text(
                "product_search_selected",
                language,
            ).format(
                name=product["name"],
                brand=brand_line,
                calories=format_number(
                    product["calories_100g"]
                ),
                protein=format_number(
                    product["protein_100g"]
                ),
                fat=format_number(
                    product["fat_100g"]
                ),
                carbs=format_number(
                    product["carbs_100g"]
                ),
            ),
            reply_markup=get_selected_product_keyboard(
                language
            ),
        )

@router.callback_query(
    ProductSearchForm.selection,
    F.data == "product_search:add_favorite",
)
async def add_selected_product_to_favorites(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")
    product = data.get("selected_product")

    if product is None:
        await callback.answer(
            "Product not found",
            show_alert=True,
        )
        return

    product_id = product.get("id")

    if product_id is None:
        await callback.answer(
            "Product is not saved locally",
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

    if created:
        text = (
            "⭐ Продукт добавлен в избранное"
            if language == "ru"
            else "⭐ Product added to favorites"
        )
    else:
        text = (
            "⭐ Этот продукт уже есть в избранном"
            if language == "ru"
            else "⭐ This product is already in favorites"
        )

    await callback.answer(
        text,
        show_alert=True,
    )
    
@router.callback_query(
    ProductSearchForm.selection,
    F.data == "product_search:enter_amount",

)
async def request_product_amount(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    selected_product = data.get("selected_product")

    if selected_product is None:
        await callback.answer(
            "Product not found",
            show_alert=True,
        )
        return

    await state.set_state(ProductSearchForm.amount)
    await callback.answer()

    if callback.message:
        if language == "ru":
            text = (
                "⚖️ Введите количество продукта "
                "в граммах:"
            )
        else:
            text = (
                "⚖️ Enter the product amount "
                "in grams:"
            )

        await callback.message.answer(text)

@router.callback_query(
    ProductSearchForm.selection,
    F.data == "product_search:add_favorite",
)
async def add_selected_product_to_favorites(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")
    product = data.get("selected_product")

    if product is None:
        await callback.answer(
            "Product not found",
            show_alert=True,
        )
        return

    product_id = product.get("id")

    if product_id is None:
        await callback.answer(
            "Product is not saved locally",
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

    if created:
        text = (
            "⭐ Продукт добавлен в избранное"
            if language == "ru"
            else "⭐ Product added to favorites"
        )
    else:
        text = (
            "⭐ Этот продукт уже есть в избранном"
            if language == "ru"
            else "⭐ This product is already in favorites"
        )

    await callback.answer(
        text,
        show_alert=True,
    )

@router.message(ProductSearchForm.amount)
async def process_product_amount(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")

    try:
        amount = float(
            (message.text or "").replace(",", ".")
        )
    except ValueError:
        await message.answer(
            get_text(
                "product_search_invalid_amount",
                language,
            )
        )
        return

    if not 1 <= amount <= 10_000:
        await message.answer(
            get_text(
                "product_search_invalid_amount",
                language,
            )
        )
        return

    product = data.get("selected_product")

    if product is None:
        await state.clear()

        await message.answer(
            get_text(
                "product_search_empty",
                language,
            )
        )
        return

    multiplier = amount / 100

    calories = round(
        product["calories_100g"] * multiplier
    )
    protein = round(
        product["protein_100g"] * multiplier,
        1,
    )
    fat = round(
        product["fat_100g"] * multiplier,
        1,
    )
    carbs = round(
        product["carbs_100g"] * multiplier,
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
            name=product["name"],
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
        )

        session.add(entry)
        await session.commit()

    await state.clear()

    await message.answer(
        get_text(
            "product_search_saved",
            language,
        ).format(
            name=product["name"],
            amount=format_number(amount),
            calories=calories,
            protein=format_number(protein),
            fat=format_number(fat),
            carbs=format_number(carbs),
        )
    )


def product_to_dict(product) -> dict:
    return {
        "id": product.id,
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        "calories_100g": product.calories_100g,
        "protein_100g": product.protein_100g,
        "fat_100g": product.fat_100g,
        "carbs_100g": product.carbs_100g,
        "source": product.source,
    }


def get_external_error_text(
    status: int,
    language: str,
) -> str:
    if status == 503:
        if language == "ru":
            return (
                "⚠️ Внешняя база продуктов временно "
                "перегружена.\n\n"
                "Локальные продукты продолжают работать. "
                "Попробуйте другой запрос или повторите позже."
            )

        return (
            "⚠️ The external product database is "
            "temporarily overloaded.\n\n"
            "Local products are still available. "
            "Try another query or try again later."
        )

    if status == 429:
        if language == "ru":
            return (
                "⏳ Выполнено слишком много запросов.\n\n"
                "Подождите немного и повторите поиск."
            )

        return (
            "⏳ Too many requests were made.\n\n"
            "Please wait and try again."
        )

    return get_text(
        "barcode_service_error",
        language,
    )


def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"