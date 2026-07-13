from app.services.metabolism import (
    ACTIVITY_FACTORS,
    calculate_bmr,
    calculate_tdee,
)


bmr = calculate_bmr(
    gender="male",
    weight=80,
    height=180,
    age=30,
)

tdee = calculate_tdee(
    bmr=bmr,
    activity_factor=ACTIVITY_FACTORS["moderate"],
)

print(f"BMR: {round(bmr)} ккал")
print(f"TDEE: {round(tdee)} ккал")