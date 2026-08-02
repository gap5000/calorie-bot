from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite_product import FavoriteProduct


async def add_favorite_product(
    session: AsyncSession,
    user_id: int,
    product_id: int,
) -> tuple[FavoriteProduct, bool]:
    result = await session.execute(
        select(FavoriteProduct).where(
            FavoriteProduct.user_id == user_id,
            FavoriteProduct.product_id == product_id,
        )
    )

    existing_favorite = result.scalar_one_or_none()

    if existing_favorite is not None:
        return existing_favorite, False

    favorite = FavoriteProduct(
        user_id=user_id,
        product_id=product_id,
    )

    session.add(favorite)
    await session.flush()

    return favorite, True


async def get_user_favorite_products(
    session: AsyncSession,
    user_id: int,
    limit: int = 50,
) -> list[FavoriteProduct]:
    result = await session.execute(
        select(FavoriteProduct)
        .options(
            selectinload(FavoriteProduct.product)
        )
        .where(
            FavoriteProduct.user_id == user_id
        )
        .order_by(
            FavoriteProduct.created_at.desc()
        )
        .limit(limit)
    )

    return list(result.scalars().all())


async def remove_favorite_product(
    session: AsyncSession,
    user_id: int,
    product_id: int,
) -> bool:
    result = await session.execute(
        delete(FavoriteProduct)
        .where(
            FavoriteProduct.user_id == user_id,
            FavoriteProduct.product_id == product_id,
        )
        .returning(FavoriteProduct.id)
    )

    deleted_id = result.scalar_one_or_none()

    return deleted_id is not None