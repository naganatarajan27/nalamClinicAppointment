import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor_availability import DoctorAvailability


class DoctorAvailabilityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_doctor(self, doctor_id: uuid.UUID) -> list[DoctorAvailability]:
        stmt = (
            select(DoctorAvailability)
            .where(DoctorAvailability.doctor_id == doctor_id)
            .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
        )
        return list(self.db.scalars(stmt))

    def list_active_for_doctor_and_day(
        self, doctor_id: uuid.UUID, day_of_week: int
    ) -> list[DoctorAvailability]:
        stmt = select(DoctorAvailability).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.day_of_week == day_of_week,
            DoctorAvailability.is_active.is_(True),
        )
        return list(self.db.scalars(stmt))

    def get(self, availability_id: uuid.UUID) -> DoctorAvailability | None:
        return self.db.get(DoctorAvailability, availability_id)

    def create(self, availability: DoctorAvailability) -> DoctorAvailability:
        self.db.add(availability)
        self.db.flush()
        return availability

    def delete(self, availability: DoctorAvailability) -> None:
        self.db.delete(availability)
