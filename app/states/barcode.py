from aiogram.fsm.state import State, StatesGroup


class BarcodeForm(StatesGroup):
    barcode = State()
    photo = State()
    amount = State()