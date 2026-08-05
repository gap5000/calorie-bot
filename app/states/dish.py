from aiogram.fsm.state import State, StatesGroup


class DishForm(StatesGroup):
    name = State()
    ingredient_search = State()
    ingredient_grams = State()