import uuid
from datetime import date, time

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus


class AppointmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.flush()
        return appointment

    def get(self, appointment_id: uuid.UUID) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def get_by_public_reference(self, public_reference: str) -> Appointment | None:
        stmt = select(Appointment).where(Appointment.public_reference == public_reference)
        return self.db.scalars(stmt).first()

    def get_by_proposed_slot_token(self, token: str) -> Appointment | None:
        stmt = select(Appointment).where(Appointment.proposed_slot_token == token)
        return self.db.scalars(stmt).first()

    def list_requested_times(self, *, doctor_id: uuid.UUID, on_date: date) -> list[time]:
        stmt = select(Appointment.requested_time).where(
            Appointment.doctor_id == doctor_id,
            Appointment.requested_date == on_date,
            Appointment.status.in_(
                [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.ALTERNATE_PROPOSED]
            ),
        )
        return list(self.db.scalars(stmt))

    def search(
        self,
        *,
        status: AppointmentStatus | None,
        date_from: date | None,
        date_to: date | None,
        query: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Appointment], int]:
        stmt = select(Appointment)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)
        if date_from is not None:
            stmt = stmt.where(Appointment.requested_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Appointment.requested_date <= date_to)
        if query:
            like = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Appointment.public_reference.ilike(like),
                    Appointment.patient_name.ilike(like),
                )
            )

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        stmt = (
            stmt.order_by(Appointment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt))
        return items, total
