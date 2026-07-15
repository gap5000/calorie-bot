from dataclasses import dataclass

import aiohttp


OPEN_FOOD_FACTS_URL = (
    "https://world.openfoodfacts.org/api/v3/product/{barcode}"
)


@dataclass(slots=True)
class ProductNutrition:
    barcode: str
    name: str
    brand: str | None
    calories_100g: float
    protein_100g: float
    fat_100g: float
    carbs_100g: float


async def get_product_by_barcode(
    barcode: str,
) -> ProductNutrition | None:
    fields = ",".join(
        [
            "code",
            "product_name",
            "product_name_ru",
            "product_name_en",
            "brands",
            "nutriments",
        ]
    )

    headers = {
        "User-Agent": (
            "CalorieBot/0.1 "
            "(contact: replace-with-your-email@example.com)"
        )
    }

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout,
    ) as session:
        async with session.get(
            OPEN_FOOD_FACTS_URL.format(barcode=barcode),
            params={"fields": fields},
        ) as response:
            if response.status == 404:
                return None

            response.raise_for_status()
            payload = await response.json()

    product = payload.get("product")

    if not product:
        return None

    nutriments = product.get("nutriments") or {}

    calories = get_float(
        nutriments,
        "energy-kcal_100g",
        "energy-kcal",
    )
    protein = get_float(nutriments, "proteins_100g")
    fat = get_float(nutriments, "fat_100g")
    carbs = get_float(nutriments, "carbohydrates_100g")

    if any(
        value is None
        for value in (calories, protein, fat, carbs)
    ):
        return None

    name = (
        product.get("product_name_ru")
        or product.get("product_name")
        or product.get("product_name_en")
        or f"Product {barcode}"
    )

    return ProductNutrition(
        barcode=barcode,
        name=name,
        brand=product.get("brands"),
        calories_100g=calories,
        protein_100g=protein,
        fat_100g=fat,
        carbs_100g=carbs,
    )

async def search_products_by_name(
    query: str,
    limit: int = 5,
) -> list[ProductNutrition]:
    url = "https://world.openfoodfacts.org/cgi/search.pl"

    params = {
        "search_terms": query,
        "search_simple": "1",
        "action": "process",
        "json": "1",
        "page_size": str(limit * 3),
        "fields": (
            "code,"
            "product_name,"
            "product_name_ru,"
            "product_name_en,"
            "brands,"
            "nutriments"
        ),
    }

    headers = {
        "User-Agent": (
            "CalorieBot/0.1 "
            "(contact: your-email@example.com)"
        )
    }

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout,
    ) as session:
        async with session.get(
            url,
            params=params,
        ) as response:
            response.raise_for_status()
            payload = await response.json(
                content_type=None
            )

    products: list[ProductNutrition] = []

    for item in payload.get("products", []):
        nutriments = item.get("nutriments") or {}

        calories = get_float(
            nutriments,
            "energy-kcal_100g",
            "energy-kcal",
        )
        protein = get_float(
            nutriments,
            "proteins_100g",
        )
        fat = get_float(
            nutriments,
            "fat_100g",
        )
        carbs = get_float(
            nutriments,
            "carbohydrates_100g",
        )

        if any(
            value is None
            for value in (
                calories,
                protein,
                fat,
                carbs,
            )
        ):
            continue

        name = (
            item.get("product_name_ru")
            or item.get("product_name")
            or item.get("product_name_en")
        )

        barcode = str(item.get("code") or "")

        if not name or not barcode:
            continue

        products.append(
            ProductNutrition(
                barcode=barcode,
                name=name,
                brand=item.get("brands"),
                calories_100g=calories,
                protein_100g=protein,
                fat_100g=fat,
                carbs_100g=carbs,
            )
        )

        if len(products) >= limit:
            break

    return products

def get_float(
    data: dict,
    *keys: str,
) -> float | None:
    for key in keys:
        value = data.get(key)

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None