from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.nutrition_entry import NutritionEntry
    from app.models.user_settings import UserSettings
    from app.models.workout import Workout

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",    
    )
    username: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    language: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,             
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    settings: Mapped["UserSettings | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    nutrition_entries: Mapped[list["NutritionEntry"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
)