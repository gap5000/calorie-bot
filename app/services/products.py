from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def get_product_by_barcode(
    session: AsyncSession,
    barcode: str,
) -> Product | None:
    normalized_barcode = barcode.strip()

    if not normalized_barcode:
        return None

    result = await session.execute(
        select(Product).where(
            Product.barcode == normalized_barcode,
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

    contains_pattern = f"%{normalized_query}%"
    starts_pattern = f"{normalized_query}%"

    relevance = case(
        (
            func.lower(Product.name)
            == normalized_query,
            0,
        ),
        (
            func.lower(Product.name).like(
                starts_pattern
            ),
            1,
        ),
        (
            func.lower(Product.name).like(
                contains_pattern
            ),
            2,
        ),
        (
            func.lower(
                func.coalesce(Product.brand, "")
            ).like(starts_pattern),
            3,
        ),
        (
            func.lower(
                func.coalesce(Product.brand, "")
            ).like(contains_pattern),
            4,
        ),
        else_=5,
    )

    result = await session.execute(
        select(Product)
        .where(
            or_(
                func.lower(Product.name).like(
                    contains_pattern
                ),
                func.lower(
                    func.coalesce(Product.brand, "")
                ).like(contains_pattern),
            )
        )
        .order_by(
            relevance,
            Product.name,
        )
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
    fiber_100g: float = 0.0,
    source: str,
) -> Product:
    normalized_name = name.strip()[:150]

    normalized_brand = (
        brand.strip()[:500]
        if brand and brand.strip()
        else None
    )

    normalized_barcode = (
        barcode.strip()[:32]
        if barcode and barcode.strip()
        else None
    )

    normalized_source = source.strip()[:32] or "manual"

    if not normalized_name:
        normalized_name = "Unnamed product"

    product: Product | None = None

    if normalized_barcode:
        product = await get_product_by_barcode(
            session=session,
            barcode=normalized_barcode,
        )

    if product is None:
        product = Product(
            name=normalized_name,
            brand=normalized_brand,
            barcode=normalized_barcode,
            calories_100g=float(calories_100g),
            protein_100g=float(protein_100g),
            fat_100g=float(fat_100g),
            carbs_100g=float(carbs_100g),
            fiber_100g=float(fiber_100g),
            source=normalized_source,
        )

        session.add(product)
        await session.flush()

        return product

    product.name = normalized_name
    product.brand = normalized_brand
    product.barcode = normalized_barcode
    product.calories_100g = float(calories_100g)
    product.protein_100g = float(protein_100g)
    product.fat_100g = float(fat_100g)
    product.carbs_100g = float(carbs_100g)
    product.fiber_100g = float(fiber_100g)
    product.source = normalized_source

    await session.flush()

    return product