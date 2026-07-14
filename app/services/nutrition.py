def calculate_calories_from_macros(
    protein: float,
    fat: float,
    carbs: float,
) -> int:
    calories = protein * 4 + fat * 9 + carbs * 4

    return round(calories)