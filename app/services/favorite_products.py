from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite_product import FavoriteProduct


async def add_favorite_product(
    session: AsyncSession,
    user_id: int,
    name: str,
    brand: str | None,
    barcode: str | None,
    calories_100g: float,
    protein_100g: float,
    fat_100g: float,
    carbs_100g: float,
) -> FavoriteProduct:
    existing_product = None

    if barcode:
        result = await session.execute(
            select(FavoriteProduct).where(
                FavoriteProduct.user_id == user_id,
                FavoriteProduct.barcode == barcode,
            )
        )
        existing_product = result.scalar_one_or_none()

    if existing_product is not None:
        return existing_product

    favorite = FavoriteProduct(
        user_id=user_id,
        name=name,
        brand=brand,
        barcode=barcode,
        calories_100g=calories_100g,
        protein_100g=protein_100g,
        fat_100g=fat_100g,
        carbs_100g=carbs_100g,
    )

    session.add(favorite)
    await session.flush()

    return favorite