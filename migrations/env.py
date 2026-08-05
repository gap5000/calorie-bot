import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Импортируем все модели, чтобы Alembic видел их
# внутри Base.metadata.
from app.models.exercise import Exercise
from app.models.favorite_product import FavoriteProduct
from app.models.nutrition_entry import NutritionEntry
from app.models.product import Product
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.workout import Workout
from app.models.workout_set import WorkoutSet
from app.models.dish import Dish
from app.models.dish_ingredient import DishIngredient
import app.models

from app.models.base import Base

target_metadata = Base.metadata
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL was not found in the .env file."
    )

config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(
    connection: Connection,
) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations
        )

    await connectable.dispose()


def run_migrations_online() -> None:
    if os.name == "nt":
        asyncio.run(
            run_async_migrations(),
            loop_factory=asyncio.SelectorEventLoop,
        )
    else:
        asyncio.run(
            run_async_migrations()
        )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()