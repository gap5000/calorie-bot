from aiogram.fsm.state import State, StatesGroup


class ExerciseForm(StatesGroup):
    name = State()
    result_weight = State()
    result_repetitions = State()