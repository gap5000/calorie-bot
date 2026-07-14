from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NutritionEntry(Base):
    __tablename__ = "nutrition_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    calories: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    protein: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    fat: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    carbs: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="nutrition_entries",
    )