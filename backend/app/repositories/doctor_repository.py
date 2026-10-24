import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor


class DoctorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active(self) -> list[Doctor]:
        stmt = select(Doctor).where(Doctor.is_active.is_(True)).order_by(Doctor.display_name)
        return list(self.db.scalars(stmt))

    def list_all(self) -> list[Doctor]:
        stmt = select(Doctor).order_by(Doctor.display_name)
        return list(self.db.scalars(stmt))

    def get(self, doctor_id: uuid.UUID) -> Doctor | None:
        return self.db.get(Doctor, doctor_id)

    def create(self, doctor: Doctor) -> Doctor:
        self.db.add(doctor)
        self.db.flush()
        return doctor
