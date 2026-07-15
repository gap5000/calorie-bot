import aiohttp

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from io import BytesIO

from app.keyboards.barcode import get_barcode_method_keyboard
from app.services.barcode_reader import read_barcode_from_image
from app.database.session import session_factory
from app.locales.texts import get_text
from app.models.nutrition_entry import NutritionEntry
from app.models.user import User
from app.services.open_food_facts import get_product_by_barcode
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

    language = await get_user_language(message.from_user.id)

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

    image_bytes = destination.getvalue()

    barcode, detected_count = read_barcode_from_image(
        image_bytes
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

    product = data["product"]
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
        get_text("barcode_entry_saved", language).format(
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
async def find_product_and_request_amount(
    message: Message,
    state: FSMContext,
    barcode: str,
    language: str,
) -> None:
    searching_message = await message.answer(
        get_text("barcode_searching", language)
    )

    try:
        product = await get_product_by_barcode(barcode)
    except (
        aiohttp.ClientError,
        TimeoutError,
    ):
        await searching_message.edit_text(
            get_text("barcode_service_error", language)
        )
        return

    if product is None:
        await searching_message.edit_text(
            get_text("barcode_not_found", language)
        )
        await state.clear()
        return

    await state.update_data(
        product={
            "barcode": product.barcode,
            "name": product.name,
            "brand": product.brand,
            "calories_100g": product.calories_100g,
            "protein_100g": product.protein_100g,
            "fat_100g": product.fat_100g,
            "carbs_100g": product.carbs_100g,
        }
    )
    await state.set_state(BarcodeForm.amount)

    brand_line = (
        f"🏷 {product.brand}\n\n"
        if product.brand
        else ""
    )

    await searching_message.edit_text(
        get_text(
            "barcode_product_found",
            language,
        ).format(
            name=product.name,
            brand=brand_line,
            calories=format_number(
                product.calories_100g
            ),
            protein=format_number(
                product.protein_100g
            ),
            fat=format_number(product.fat_100g),
            carbs=format_number(
                product.carbs_100g
            ),
        )
    )