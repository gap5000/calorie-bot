from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.favorites import (
    get_favorites_keyboard,
    get_remove_favorites_keyboard,
)
from app.keyboards.nutrition import get_nutrition_keyboard
from app.models.nutrition_entry import NutritionEntry
from app.models.product import Product
from app.models.user import User
from app.services.favorite_products import (
    get_user_favorite_products,
    remove_favorite_product,
)
from app.services.users import get_user_language

router = Router(name=__name__)


class FavoriteForm(StatesGroup):
    amount = State()


@router.message(
    F.text.in_(
        {
            "⭐ Избранное",
            "⭐ Favorites",
        }
    )
)
async def show_favorites(
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

        favorites = await get_user_favorite_products(
            session=session,
            user_id=user.id,
        )

    if not favorites:
        if language == "ru":
            text = (
                "⭐ <b>Избранное пусто</b>\n\n"
                "Добавьте продукт в избранное через "
                "поиск или штрихкод."
            )
        else:
            text = (
                "⭐ <b>Favorites are empty</b>\n\n"
                "Add a product through search "
                "or barcode scanning."
            )
    else:
        if language == "ru":
            text = (
                "⭐ <b>Избранные продукты</b>\n\n"
                "Выберите продукт:"
            )
        else:
            text = (
                "⭐ <b>Favorite products</b>\n\n"
                "Choose a product:"
            )

    await message.answer(
        text,
        reply_markup=get_favorites_keyboard(
            favorites=favorites,
            language=language,
        ),
    )


@router.callback_query(
    F.data.startswith("favorite:select:")
)
async def select_favorite_product(
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
        product_id = int(
            callback.data.split(":")[2]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Product not found",
            show_alert=True,
        )
        return

    async with session_factory() as session:
        result = await session.execute(
            select(Product).where(
                Product.id == product_id
            )
        )

        product = result.scalar_one_or_none()

        if product is None:
            await callback.answer(
                "Product not found",
                show_alert=True,
            )
            return

        await state.update_data(
            language=language,
            favorite_product={
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "calories_100g": product.calories_100g,
                "protein_100g": product.protein_100g,
                "fat_100g": product.fat_100g,
                "carbs_100g": product.carbs_100g,
            },
        )

    await state.set_state(FavoriteForm.amount)
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


@router.message(FavoriteForm.amount)
async def process_favorite_amount(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    data = await state.get_data()
    language = data.get("language", "en")
    product = data.get("favorite_product")

    if product is None:
        await state.clear()

        await message.answer(
            "Product not found."
        )
        return

    try:
        amount = float(
            (message.text or "").replace(",", ".")
        )
    except ValueError:
        await message.answer(
            (
                "Введите число от 1 до 10000."
                if language == "ru"
                else "Enter a number from 1 to 10000."
            )
        )
        return

    if not 1 <= amount <= 10_000:
        await message.answer(
            (
                "Введите число от 1 до 10000."
                if language == "ru"
                else "Enter a number from 1 to 10000."
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

    if language == "ru":
        text = (
            "✅ <b>Продукт добавлен</b>\n\n"
            f"🍽 {product['name']}\n"
            f"⚖️ {format_number(amount)} г\n"
            f"🔥 {calories} ккал\n"
            f"🥩 Белки: {format_number(protein)} г\n"
            f"🥑 Жиры: {format_number(fat)} г\n"
            f"🍚 Углеводы: {format_number(carbs)} г"
        )
    else:
        text = (
            "✅ <b>Product added</b>\n\n"
            f"🍽 {product['name']}\n"
            f"⚖️ {format_number(amount)} g\n"
            f"🔥 {calories} kcal\n"
            f"🥩 Protein: {format_number(protein)} g\n"
            f"🥑 Fat: {format_number(fat)} g\n"
            f"🍚 Carbohydrates: "
            f"{format_number(carbs)} g"
        )

    await message.answer(
        text,
        reply_markup=get_nutrition_keyboard(language),
    )


@router.callback_query(
    F.data == "favorite:remove_menu"
)
async def show_remove_favorites_menu(
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

        favorites = await get_user_favorite_products(
            session=session,
            user_id=user.id,
        )

    await callback.answer()

    if callback.message:
        text = (
            "🗑 <b>Удаление из избранного</b>\n\n"
            "Выберите продукт, который хотите удалить:"
            if language == "ru"
            else (
                "🗑 <b>Remove from favorites</b>\n\n"
                "Choose a product to remove:"
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_remove_favorites_keyboard(
                favorites=favorites,
                language=language,
            ),
        )

@router.callback_query(
    F.data.startswith("favorite:remove:")
)
async def delete_favorite_product(
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
        product_id = int(
            callback.data.split(":")[2]
        )
    except (ValueError, IndexError):
        await callback.answer(
            "Product not found",
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

        deleted = await remove_favorite_product(
            session=session,
            user_id=user.id,
            product_id=product_id,
        )

        await session.commit()

        favorites = await get_user_favorite_products(
            session=session,
            user_id=user.id,
        )

    if not deleted:
        await callback.answer(
            (
                "Продукт уже удалён"
                if language == "ru"
                else "Product is already removed"
            ),
            show_alert=True,
        )
        return

    await callback.answer(
        (
            "✅ Продукт удалён"
            if language == "ru"
            else "✅ Product removed"
        ),
        show_alert=True,
    )

    if callback.message:
        if favorites:
            text = (
                "🗑 <b>Удаление из избранного</b>\n\n"
                "Выберите следующий продукт:"
                if language == "ru"
                else (
                    "🗑 <b>Remove from favorites</b>\n\n"
                    "Choose another product:"
                )
            )

            await callback.message.edit_text(
                text,
                reply_markup=get_remove_favorites_keyboard(
                    favorites=favorites,
                    language=language,
                ),
            )
        else:
            text = (
                "⭐ <b>Избранное пусто</b>\n\n"
                "Все продукты удалены."
                if language == "ru"
                else (
                    "⭐ <b>Favorites are empty</b>\n\n"
                    "All products were removed."
                )
            )

            await callback.message.edit_text(
                text,
                reply_markup=get_favorites_keyboard(
                    favorites=[],
                    language=language,
                ),
            )

@router.callback_query(
    F.data == "favorite:remove_back"
)
async def back_from_remove_menu(
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

        favorites = await get_user_favorite_products(
            session=session,
            user_id=user.id,
        )

    await callback.answer()

    if callback.message:
        text = (
            "⭐ <b>Избранные продукты</b>\n\n"
            "Выберите продукт:"
            if language == "ru"
            else (
                "⭐ <b>Favorite products</b>\n\n"
                "Choose a product:"
            )
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_favorites_keyboard(
                favorites=favorites,
                language=language,
            ),
        )

@router.callback_query(
    F.data == "favorite:back"
)
async def back_to_nutrition(
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
            "🍽 Вы вернулись в раздел питания."
            if language == "ru"
            else "🍽 You returned to nutrition."
        )

        await callback.message.answer(
            text,
            reply_markup=get_nutrition_keyboard(language),
        )


def format_number(value: float) -> str:
    number = float(value)

    if number.is_integer():
        return str(int(number))

    return f"{number:.1f}"