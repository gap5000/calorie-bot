from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.favorite_product import FavoriteProduct


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(32),
        unique=True,
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    brand: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    calories_100g: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    protein_100g: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    fat_100g: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    carbs_100g: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(32),
        default="manual",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    favorites: Mapped[list["FavoriteProduct"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )