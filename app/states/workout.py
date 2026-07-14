from aiogram.fsm.state import State, StatesGroup


class WorkoutForm(StatesGroup):
    category = State()
    exercise = State()
    custom_exercise = State()
    weight = State()
    repetitions = State()
    next_action = State()