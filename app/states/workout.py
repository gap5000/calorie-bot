from aiogram.fsm.state import State, StatesGroup


class WorkoutForm(StatesGroup):
    exercise_name = State()
    weight = State()
    repetitions = State()
    next_action = State()