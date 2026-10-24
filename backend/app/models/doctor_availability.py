import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DoctorAvailability(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recurring weekly availability window for a doctor.

    e.g. "Dr. Rao is available Mondays 09:00-13:00 in 30-minute slots."
    `availability_service` expands these into bookable slots for a given date.
    """

    __tablename__ = "doctor_availabilities"

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("doctors.id"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
