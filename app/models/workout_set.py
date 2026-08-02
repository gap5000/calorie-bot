from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.exercise import Exercise
    from app.models.workout import Workout


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    workout_id: Mapped[int] = mapped_column(
        ForeignKey(
            "workouts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    exercise_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "exercises.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    exercise_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    set_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    repetitions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    workout: Mapped["Workout"] = relationship(
        back_populates="sets",
    )

    exercise: Mapped["Exercise | None"] = relationship(
        back_populates="workout_sets",
    )