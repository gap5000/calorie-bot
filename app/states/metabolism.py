from aiogram.fsm.state import State, StatesGroup


class MetabolismForm(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    activity = State()