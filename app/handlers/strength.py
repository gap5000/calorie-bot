from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.main import get_main_keyboard
from app.keyboards.strength import get_strength_keyboard
from app.locales.texts import get_text
from app.services.users import get_user_language

router = Router(name=__name__)


@router.message(
    F.text.in_(
        {
            "💪 Силовые",
            "💪 Strength training",
        }
    )
)
async def strength_menu_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    if language == "ru":
        text = (
            "💪 <b>Силовые тренировки</b>\n\n"
            "Здесь можно вести дневник упражнений, "
            "следить за прогрессией нагрузки "
            "и смотреть личные рекорды."
        )
    else:
        text = (
            "💪 <b>Strength training</b>\n\n"
            "Here you can keep an exercise diary, "
            "track load progression "
            "and view personal records."
        )

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "📓 Дневник тренировок",
            "📓 Workout diary",
        }
    )
)
async def workout_diary_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    if language == "ru":
        text = (
            "📓 <b>Дневник тренировок</b>\n\n"
            "Здесь будут храниться результаты "
            "по каждому упражнению.\n\n"
            "Функцию подключим следующим шагом."
        )
    else:
        text = (
            "📓 <b>Workout diary</b>\n\n"
            "Your exercise results will be stored here.\n\n"
            "We will connect this feature next."
        )

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "📈 Прогрессия нагрузки",
            "📈 Load progression",
        }
    )
)
async def load_progression_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    if language == "ru":
        text = (
            "📈 <b>Прогрессия нагрузки</b>\n\n"
            "Здесь будет отображаться изменение "
            "веса, повторений и тренировочного объёма "
            "по каждому упражнению.\n\n"
            "Функцию подключим после дневника."
        )
    else:
        text = (
            "📈 <b>Load progression</b>\n\n"
            "Changes in weight, repetitions "
            "and training volume will be shown here.\n\n"
            "We will connect this after the diary."
        )

    await message.answer(
        text,
        reply_markup=get_strength_keyboard(language),
    )


@router.message(
    F.text.in_(
        {
            "⬅️ Главное меню",
            "⬅️ Main menu",
        }
    )
)
async def back_to_main_menu_handler(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    language = await get_user_language(
        message.from_user.id
    )

    await message.answer(
        get_text("main_menu", language),
        reply_markup=get_main_keyboard(language),
    )