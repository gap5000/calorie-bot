import aiohttp

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.services.open_food_facts import (
    search_products_by_name as search_external_products,
)
from app.services.products import (
    create_or_update_product,
    search_products_by_name as search_local_products,
)


async def search_and_cache_products(
    session: AsyncSession,
    query: str,
    limit: int = 5,
) -> list[Product]:
    """
    Общий поиск продуктов.

    Алгоритм:

    1. Ищем в локальной PostgreSQL.
    2. Если нашли — сразу возвращаем.
    3. Если нет — ищем в Open Food Facts.
    4. Всё найденное сохраняем локально.
    5. Возвращаем уже сохранённые продукты.
    """

    local_products = await search_local_products(
        session=session,
        query=query,
        limit=limit,
    )

    if local_products:
        return local_products

    external_products = await search_external_products(
        query=query,
        limit=limit,
    )

    if not external_products:
        return []

    saved_products = []

    for product in external_products:
        saved_product = await create_or_update_product(
            session=session,
            name=product.name,
            brand=product.brand,
            barcode=product.barcode,
            calories_100g=product.calories_100g,
            protein_100g=product.protein_100g,
            fat_100g=product.fat_100g,
            carbs_100g=product.carbs_100g,
            fiber_100g=getattr(
                product,
                "fiber_100g",
                0.0,
            ),
            source="open_food_facts",
        )

        saved_products.append(saved_product)

    await session.commit()

    return saved_products