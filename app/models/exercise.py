from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workout_set import WorkoutSet


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="exercises",
    )

    workout_sets: Mapped[list["WorkoutSet"]] = relationship(
        back_populates="exercise",
    )