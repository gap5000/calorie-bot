from aiogram.fsm.state import State, StatesGroup


class NutritionGoalForm(StatesGroup):
    calories = State()
    protein = State()
    fat = State()
    carbs = State()
    period = State()