import aiohttp

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.product_search import (
    get_product_results_keyboard,
)
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.services.open_food_facts import (
    search_products_by_name,
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

    try:
        found_products = await search_products_by_name(
            query=query,
            limit=5,
        )
    except (
        aiohttp.ClientError,
        TimeoutError,
    ):
        await searching_message.edit_text(
            get_text(
                "barcode_service_error",
                language,
            )
        )
        return

    if not found_products:
        await searching_message.edit_text(
            get_text(
                "product_search_empty",
                language,
            )
        )
        return

    products = [
        {
            "barcode": product.barcode,
            "name": product.name,
            "brand": product.brand,
            "calories_100g": product.calories_100g,
            "protein_100g": product.protein_100g,
            "fat_100g": product.fat_100g,
            "carbs_100g": product.carbs_100g,
        }
        for product in found_products
    ]

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
            get_text("product_search_intro", language)
        )


@router.callback_query(
    ProductSearchForm.selection,
    F.data.startswith("product_search:"),
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
    await state.set_state(ProductSearchForm.amount)

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
            )
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

    product = data["selected_product"]
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


def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"