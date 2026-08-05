from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish
from app.models.dish_ingredient import DishIngredient
from app.models.product import Product


class DishNutrition(TypedDict):
    total_grams: float
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float
    calories_100g: float
    protein_100g: float
    fat_100g: float
    carbs_100g: float
    fiber_100g: float


async def get_user_dishes(
    session: AsyncSession,
    user_id: int,
) -> list[Dish]:
    result = await session.execute(
        select(Dish)
        .where(
            Dish.user_id == user_id
        )
        .order_by(
            Dish.name
        )
    )

    return list(result.scalars().all())


async def get_user_dish(
    session: AsyncSession,
    user_id: int,
    dish_id: int,
) -> Dish | None:
    result = await session.execute(
        select(Dish)
        .options(
            selectinload(Dish.ingredients)
            .selectinload(DishIngredient.product)
        )
        .where(
            Dish.id == dish_id,
            Dish.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()


async def create_dish(
    session: AsyncSession,
    user_id: int,
    name: str,
) -> Dish:
    dish = Dish(
        user_id=user_id,
        name=name,
    )

    session.add(dish)
    await session.flush()

    return dish


async def add_dish_ingredient(
    session: AsyncSession,
    dish_id: int,
    product_id: int,
    grams: float,
) -> DishIngredient:
    ingredient = DishIngredient(
        dish_id=dish_id,
        product_id=product_id,
        grams=grams,
    )

    session.add(ingredient)
    await session.flush()

    return ingredient


async def delete_dish(
    session: AsyncSession,
    dish: Dish,
) -> None:
    await session.delete(dish)


def calculate_dish_nutrition(
    dish: Dish,
) -> DishNutrition:
    total_grams = 0.0
    calories = 0.0
    protein = 0.0
    fat = 0.0
    carbs = 0.0
    fiber = 0.0

    for ingredient in dish.ingredients:
        product: Product = ingredient.product
        multiplier = ingredient.grams / 100

        total_grams += ingredient.grams
        calories += product.calories_100g * multiplier
        protein += product.protein_100g * multiplier
        fat += product.fat_100g * multiplier
        carbs += product.carbs_100g * multiplier
        fiber += product.fiber_100g * multiplier

    if total_grams > 0:
        per_100g_multiplier = 100 / total_grams

        calories_100g = calories * per_100g_multiplier
        protein_100g = protein * per_100g_multiplier
        fat_100g = fat * per_100g_multiplier
        carbs_100g = carbs * per_100g_multiplier
        fiber_100g = fiber * per_100g_multiplier
    else:
        calories_100g = 0.0
        protein_100g = 0.0
        fat_100g = 0.0
        carbs_100g = 0.0
        fiber_100g = 0.0

    return {
        "total_grams": round(total_grams, 1),
        "calories": round(calories, 1),
        "protein": round(protein, 1),
        "fat": round(fat, 1),
        "carbs": round(carbs, 1),
        "fiber": round(fiber, 1),
        "calories_100g": round(calories_100g, 1),
        "protein_100g": round(protein_100g, 1),
        "fat_100g": round(fat_100g, 1),
        "carbs_100g": round(carbs_100g, 1),
        "fiber_100g": round(fiber_100g, 1),
    }