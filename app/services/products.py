from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def get_product_by_barcode(
    session: AsyncSession,
    barcode: str,
) -> Product | None:
    result = await session.execute(
        select(Product).where(
            Product.barcode == barcode,
        )
    )

    return result.scalar_one_or_none()


async def search_products_by_name(
    session: AsyncSession,
    query: str,
    limit: int = 5,
) -> list[Product]:
    normalized_query = query.strip().lower()

    if not normalized_query:
        return []

    result = await session.execute(
        select(Product)
        .where(
            func.lower(Product.name).contains(
                normalized_query
            )
        )
        .order_by(Product.name)
        .limit(limit)
    )

    return list(result.scalars().all())


async def create_or_update_product(
    session: AsyncSession,
    *,
    name: str,
    brand: str | None,
    barcode: str | None,
    calories_100g: float,
    protein_100g: float,
    fat_100g: float,
    carbs_100g: float,
    source: str,
) -> Product:
    product = None

    if barcode:
        product = await get_product_by_barcode(
            session=session,
            barcode=barcode,
        )

    if product is None:
        product = Product(
            name=name,
            brand=brand,
            barcode=barcode,
            calories_100g=calories_100g,
            protein_100g=protein_100g,
            fat_100g=fat_100g,
            carbs_100g=carbs_100g,
            source=source,
        )

        session.add(product)
        await session.flush()

        return product

    product.name = name
    product.brand = brand
    product.calories_100g = calories_100g
    product.protein_100g = protein_100g
    product.fat_100g = fat_100g
    product.carbs_100g = carbs_100g
    product.source = source

    await session.flush()

    return product