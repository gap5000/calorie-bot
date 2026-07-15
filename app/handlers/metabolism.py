from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.services.users import get_user_language
from app.keyboards.navigation import get_back_to_main_keyboard
from app.keyboards.main import get_main_keyboard

from app.keyboards.metabolism import (
    activity_keyboard,
    gender_keyboard,
)
from app.locales.texts import get_text
from app.services.metabolism import (
    ACTIVITY_FACTORS,
    calculate_bmr,
    calculate_tdee,
)
from app.states.metabolism import MetabolismForm

router = Router(name=__name__)

@router.message(
    F.text.in_(
        {
            "🔥 Рассчитать норму",
            "🔥 Calculate daily needs",
        }
    )
)
async def start_metabolism_calculation(
    message: Message,
    state: FSMContext,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(message.from_user.id)

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(MetabolismForm.gender)

    await message.answer(
    get_text("metabolism_intro", language),
    reply_markup=gender_keyboard,
)

    await message.answer(
    (
        "Вы можете отменить расчёт в любой момент."
        if language == "ru"
        else "You can cancel the calculation at any time."
    ),
    reply_markup=get_back_to_main_keyboard(language),
)


@router.callback_query(
    MetabolismForm.gender,
    F.data.startswith("metabolism_gender:"),
)
async def process_gender(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    gender = callback.data.split(":")[1]

    if gender not in {"male", "female"}:
        await callback.answer("Unsupported value")
        return

    await state.update_data(gender=gender)
    await state.set_state(MetabolismForm.age)

    data = await state.get_data()
    language = data.get("language", "en")

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("enter_age", language)
        )


@router.message(MetabolismForm.age)
async def process_age(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        age = int(message.text or "")
    except ValueError:
        await message.answer(get_text("invalid_age", language))
        return

    if not 14 <= age <= 100:
        await message.answer(get_text("invalid_age", language))
        return

    await state.update_data(age=age)
    await state.set_state(MetabolismForm.height)

    await message.answer(get_text("enter_height", language))


@router.message(MetabolismForm.height)
async def process_height(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        height = float(
            (message.text or "").replace(",", ".")
        )
    except ValueError:
        await message.answer(get_text("invalid_height", language))
        return

    if not 100 <= height <= 250:
        await message.answer(get_text("invalid_height", language))
        return

    await state.update_data(height=height)
    await state.set_state(MetabolismForm.weight)

    await message.answer(get_text("enter_weight", language))


@router.message(MetabolismForm.weight)
async def process_weight(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    language = data.get("language", "en")

    try:
        weight = float(
            (message.text or "").replace(",", ".")
        )
    except ValueError:
        await message.answer(get_text("invalid_weight", language))
        return

    if not 30 <= weight <= 350:
        await message.answer(get_text("invalid_weight", language))
        return

    await state.update_data(weight=weight)
    await state.set_state(MetabolismForm.activity)

    await message.answer(
        get_text("choose_activity", language),
        reply_markup=activity_keyboard,
    )


@router.callback_query(
    MetabolismForm.activity,
    F.data.startswith("metabolism_activity:"),
)
async def process_activity(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    activity = callback.data.split(":")[1]

    if activity not in ACTIVITY_FACTORS:
        await callback.answer("Unsupported value")
        return

    data = await state.get_data()

    language = data.get("language", "en")
    gender = data["gender"]
    age = data["age"]
    height = data["height"]
    weight = data["weight"]

    bmr = calculate_bmr(
        gender=gender,
        weight=weight,
        height=height,
        age=age,
    )

    tdee = calculate_tdee(
        bmr=bmr,
        activity_factor=ACTIVITY_FACTORS[activity],
    )

    await callback.answer()
    await state.clear()

    if callback.message is None:
        return

    if language == "ru":
        result_text = (
            "📊 <b>Результат расчёта</b>\n\n"
            f"🔥 Базовый обмен: <b>{round(bmr)} ккал</b>\n"
            f"⚡ С учётом активности: "
            f"<b>{round(tdee)} ккал</b>\n\n"
            "Расчёт является ориентировочным и "
            "не заменяет консультацию специалиста."
        )
    else:
        result_text = (
            "📊 <b>Calculation result</b>\n\n"
            f"🔥 Basal metabolic rate: "
            f"<b>{round(bmr)} kcal</b>\n"
            f"⚡ With activity included: "
            f"<b>{round(tdee)} kcal</b>\n\n"
            "This is an estimate and does not replace "
            "professional medical advice."
        )

    await callback.message.answer(
    result_text,
    reply_markup=get_main_keyboard(language),
)