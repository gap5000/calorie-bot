from aiogram.fsm.state import State, StatesGroup


class ProductSearchForm(StatesGroup):
    query = State()
    selection = State()
    amount = State()