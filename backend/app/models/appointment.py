import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AppointmentStatus, PatientType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Appointment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    public_reference: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )

    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_type: Mapped[PatientType] = mapped_column(
        Enum(PatientType, native_enum=False, length=32), nullable=False
    )
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    whatsapp_number: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("doctors.id"), nullable=False, index=True
    )
    requested_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    requested_time: Mapped[time] = mapped_column(Time, nullable=False)

    confirmed_doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("doctors.id"), nullable=True
    )
    confirmed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmed_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    proposed_doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("doctors.id"), nullable=True
    )
    proposed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    proposed_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    proposed_slot_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    proposed_slot_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    symptoms: Mapped[str] = mapped_column(String(1000), nullable=False)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, native_enum=False, length=32),
        nullable=False,
        default=AppointmentStatus.PENDING,
        index=True,
    )

    admin_note: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    reviewed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("admins.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
