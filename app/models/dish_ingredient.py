from typing import TYPE_CHECKING

from sqlalchemy import (
    Float,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dish import Dish
    from app.models.product import Product


class DishIngredient(Base):
    __tablename__ = "dish_ingredients"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    dish_id: Mapped[int] = mapped_column(
        ForeignKey(
            "dishes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    grams: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    dish: Mapped["Dish"] = relationship(
        back_populates="ingredients",
    )

    product: Mapped["Product"] = relationship()