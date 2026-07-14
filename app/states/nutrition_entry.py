from aiogram.fsm.state import State, StatesGroup


class NutritionEntryForm(StatesGroup):
    name = State()
    calories = State()
    protein = State()
    fat = State()
    carbs = State()