import aiohttp

from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database.session import session_factory
from app.keyboards.barcode import get_barcode_method_keyboard
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.services.barcode_reader import read_barcode_from_image
from app.services.open_food_facts import (
    get_product_by_barcode as get_external_product_by_barcode,
)
from app.services.products import (
    create_or_update_product,
    get_product_by_barcode as get_local_product_by_barcode,
)
from app.services.users import get_user_language
from app.states.barcode import BarcodeForm

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "📦 Добавить по штрихкоду",
            "📦 Add by barcode",
        }
    )
)
async def start_barcode_entry(
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

    await message.answer(
        get_text("barcode_choose_method", language),
        reply_markup=get_barcode_method_keyboard(language),
    )


@router.callback_query(
    F.data == "barcode_method:digits"
)
async def choose_barcode_digits(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    await state.set_state(BarcodeForm.barcode)
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("barcode_intro", language)
        )


@router.callback_query(
    F.data == "barcode_method:photo"
)
async def choose_barcode_photo(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    await state.set_state(BarcodeForm.photo)
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("barcode_send_photo", language)
        )


@router.message(BarcodeForm.barcode)
async def process_barcode(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    barcode = "".join(
        character
        for character in (message.text or "")
        if character.isdigit()
    )

    if not 8 <= len(barcode) <= 14:
        await message.answer(
            get_text("barcode_invalid", language)
        )
        return

    await find_product_and_request_amount(
        message=message,
        state=state,
        barcode=barcode,
        language=language,
    )


@router.message(
    BarcodeForm.photo,
    F.photo,
)
async def process_barcode_photo(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    if not message.photo:
        await message.answer(
            get_text("barcode_photo_required", language)
        )
        return

    largest_photo = message.photo[-1]
    destination = BytesIO()

    await message.bot.download(
        largest_photo,
        destination=destination,
    )

    barcode, detected_count = read_barcode_from_image(
        destination.getvalue()
    )

    if barcode is None:
        await message.answer(
            get_text("barcode_not_detected", language)
        )
        return

    if detected_count > 1:
        await message.answer(
            get_text(
                "barcode_multiple_detected",
                language,
            ).format(barcode=barcode)
        )

    await message.answer(
        f"🔢 <b>{barcode}</b>"
    )

    await find_product_and_request_amount(
        message=message,
        state=state,
        barcode=barcode,
        language=language,
    )


@router.message(BarcodeForm.photo)
async def process_invalid_barcode_photo(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    await message.answer(
        get_text("barcode_photo_required", language)
    )


@router.message(BarcodeForm.amount)
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
            get_text("barcode_invalid_amount", language)
        )
        return

    if not 1 <= amount <= 10_000:
        await message.answer(
            get_text("barcode_invalid_amount", language)
        )
        return

    product = data.get("product")

    if product is None:
        await state.clear()

        await message.answer(
            get_text("barcode_not_found", language)
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
            "barcode_entry_saved",
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


async def find_product_and_request_amount(
    message: Message,
    state: FSMContext,
    barcode: str,
    language: str,
) -> None:
    searching_message = await message.answer(
        get_text("barcode_searching", language)
    )

    async with session_factory() as session:
        local_product = await get_local_product_by_barcode(
            session=session,
            barcode=barcode,
        )

        if local_product is not None:
            await prepare_product_for_amount(
                searching_message=searching_message,
                state=state,
                product=product_to_dict(local_product),
                language=language,
            )
            return

        try:
            external_product = (
                await get_external_product_by_barcode(
                    barcode
                )
            )
        except aiohttp.ClientResponseError as error:
            print(
                "Open Food Facts barcode response error:",
                error.status,
                repr(error),
            )

            await searching_message.edit_text(
                get_barcode_error_text(
                    status=error.status,
                    language=language,
                )
            )
            return
        except (
            aiohttp.ClientError,
            TimeoutError,
        ) as error:
            print(
                "Open Food Facts barcode connection error:",
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

        if external_product is None:
            await searching_message.edit_text(
                get_text("barcode_not_found", language)
            )
            await state.clear()
            return

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

        await session.commit()

        product_data = product_to_dict(saved_product)

    await prepare_product_for_amount(
        searching_message=searching_message,
        state=state,
        product=product_data,
        language=language,
    )


async def prepare_product_for_amount(
    searching_message: Message,
    state: FSMContext,
    product: dict,
    language: str,
) -> None:
    await state.update_data(product=product)
    await state.set_state(BarcodeForm.amount)

    brand_line = (
        f"🏷 {product['brand']}\n\n"
        if product.get("brand")
        else ""
    )

    await searching_message.edit_text(
        get_text(
            "barcode_product_found",
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


def get_barcode_error_text(
    status: int,
    language: str,
) -> str:
    if status == 503:
        if language == "ru":
            return (
                "⚠️ Внешняя база продуктов временно "
                "недоступна.\n\n"
                "Если продукт уже сканировали раньше, "
                "он продолжит работать из локальной базы."
            )

        return (
            "⚠️ The external product database is "
            "temporarily unavailable.\n\n"
            "Previously scanned products still work "
            "from the local database."
        )

    if status == 429:
        if language == "ru":
            return (
                "⏳ Выполнено слишком много запросов.\n\n"
                "Подождите немного и повторите попытку."
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