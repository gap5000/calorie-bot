from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.meal_type import get_meal_type_keyboard
from app.states.nutrition_flow import NutritionFlow

from aiogram.types import Message

from app.keyboards.nutrition import get_nutrition_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "🍽 Питание",
            "🍽 Nutrition",
        }
    )
)
async def nutrition_menu_handler(
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
        "🍽 <b>Питание</b>\n\n"
        "Выберите действие:"
        if language == "ru"
        else (
            "🍽 <b>Nutrition</b>\n\n"
            "Choose an action:"
        )
    )

    await message.answer(
        text,
        reply_markup=get_nutrition_keyboard(language),
    )


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

    language = await get_user_language(
        message.from_user.id
    )

    await state.clear()
    await state.update_data(language=language)
    await state.set_state(NutritionFlow.meal_type)

    text = (
        "🍽 <b>Выберите приём пищи:</b>"
        if language == "ru"
        else "🍽 <b>Choose a meal:</b>"
    )

    await message.answer(
        text,
        reply_markup=get_meal_type_keyboard(
            language=language,
            callback_prefix="nutrition_meal",
        ),
    )

@router.callback_query(
    NutritionFlow.meal_type,
    F.data.regexp(
        r"^nutrition_meal:"
        r"(breakfast|lunch|dinner|snack)$"
    ),
)
async def select_nutrition_meal_type(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data is None:
        await callback.answer()
        return

    data = await state.get_data()
    language = data.get("language", "en")

    meal_type = callback.data.split(":")[1]

    await state.update_data(
        meal_type=meal_type,
    )
    await state.set_state(None)
    await callback.answer()

    text = (
        "➕ <b>Добавить питание</b>\n\n"
        "Выберите способ добавления:"
        if language == "ru"
        else (
            "➕ <b>Add nutrition</b>\n\n"
            "Choose how to add food:"
        )
    )

    if callback.message:
        await callback.message.answer(
            text,
            reply_markup=get_nutrition_keyboard(language),
        )

@router.callback_query(
    NutritionFlow.meal_type,
    F.data == "nutrition_meal:cancel",
)
async def cancel_nutrition_entry(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    language = await get_user_language(
        callback.from_user.id
    )

    await state.clear()
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            (
                "❌ Добавление питания отменено."
                if language == "ru"
                else "❌ Nutrition entry cancelled."
            ),
            reply_markup=get_nutrition_keyboard(language),
        )