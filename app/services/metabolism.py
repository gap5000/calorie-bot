from typing import Literal


Gender = Literal["male", "female"]

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "very_high": 1.9,
}

def calculate_bmr(
    gender: Gender,
    weight: float,
    height: float,
    age: int,
) -> float:
    base_value = 10 * weight + 6.25 * height - 5 * age

    if gender == "male":
        return base_value + 5

    return base_value - 161


def calculate_tdee(
    bmr: float,
    activity_factor: float,
) -> float:
    return bmr * activity_factor