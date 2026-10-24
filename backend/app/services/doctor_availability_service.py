import uuid

from sqlalchemy.orm import Session

from app.models.doctor_availability import DoctorAvailability
from app.repositories.doctor_availability_repository import DoctorAvailabilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor_availability import DoctorAvailabilityCreate, DoctorAvailabilityUpdate
from app.services.exceptions import NotFoundError, ValidationError


def list_for_doctor(db: Session, doctor_id: uuid.UUID) -> list[DoctorAvailability]:
    if DoctorRepository(db).get(doctor_id) is None:
        raise NotFoundError("Doctor not found.")
    return DoctorAvailabilityRepository(db).list_for_doctor(doctor_id)


def create(db: Session, doctor_id: uuid.UUID, payload: DoctorAvailabilityCreate) -> DoctorAvailability:
    if DoctorRepository(db).get(doctor_id) is None:
        raise NotFoundError("Doctor not found.")

    availability = DoctorAvailability(
        doctor_id=doctor_id,
        day_of_week=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        slot_duration_minutes=payload.slot_duration_minutes,
        is_active=payload.is_active,
    )
    DoctorAvailabilityRepository(db).create(availability)
    db.commit()
    return availability


def update(
    db: Session, doctor_id: uuid.UUID, availability_id: uuid.UUID, payload: DoctorAvailabilityUpdate
) -> DoctorAvailability:
    repo = DoctorAvailabilityRepository(db)
    availability = repo.get(availability_id)
    if availability is None or availability.doctor_id != doctor_id:
        raise NotFoundError("Availability window not found.")

    if payload.day_of_week is not None:
        availability.day_of_week = payload.day_of_week
    if payload.start_time is not None:
        availability.start_time = payload.start_time
    if payload.end_time is not None:
        availability.end_time = payload.end_time
    if payload.slot_duration_minutes is not None:
        availability.slot_duration_minutes = payload.slot_duration_minutes
    if payload.is_active is not None:
        availability.is_active = payload.is_active

    if availability.start_time >= availability.end_time:
        raise ValidationError("Start time must be before end time.")

    db.commit()
    return availability


def delete(db: Session, doctor_id: uuid.UUID, availability_id: uuid.UUID) -> None:
    repo = DoctorAvailabilityRepository(db)
    availability = repo.get(availability_id)
    if availability is None or availability.doctor_id != doctor_id:
        raise NotFoundError("Availability window not found.")
    repo.delete(availability)
    db.commit()
