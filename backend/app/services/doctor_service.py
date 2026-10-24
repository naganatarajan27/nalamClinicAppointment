from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import DoctorCreate


def list_active_doctors(db: Session) -> list[Doctor]:
    return DoctorRepository(db).list_active()


def list_all_doctors(db: Session) -> list[Doctor]:
    return DoctorRepository(db).list_all()


def create_doctor(db: Session, payload: DoctorCreate) -> Doctor:
    doctor = Doctor(
        display_name=payload.display_name,
        specialty=payload.specialty,
        is_active=payload.is_active,
    )
    doctor = DoctorRepository(db).create(doctor)
    db.commit()
    return doctor
