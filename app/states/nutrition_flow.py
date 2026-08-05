from aiogram.fsm.state import State, StatesGroup


class NutritionFlow(StatesGroup):
    meal_type = State()