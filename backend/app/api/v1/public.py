import uuid
from datetime import date, time

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import DbSession
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentCreated,
    AppointmentPublicStatus,
    ConfirmProposedSlotRequest,
)
from app.schemas.doctor import DoctorPublic
from app.services import appointment_service, availability_service, doctor_service
from app.services.exceptions import InvalidTransitionError, NotFoundError, ValidationError

router = APIRouter(tags=["public"])


class AvailabilityResponse(BaseModel):
    doctor_id: uuid.UUID
    date: date
    available_times: list[time]


@router.get("/doctors", response_model=list[DoctorPublic])
def list_doctors(db: DbSession) -> list[DoctorPublic]:
    doctors = doctor_service.list_active_doctors(db)
    return [DoctorPublic.model_validate(d) for d in doctors]


@router.get("/availability", response_model=AvailabilityResponse)
def get_availability(
    db: DbSession,
    doctor_id: uuid.UUID = Query(...),
    date_: date = Query(..., alias="date"),
) -> AvailabilityResponse:
    slots = availability_service.list_available_slots(db, doctor_id=doctor_id, on_date=date_)
    return AvailabilityResponse(doctor_id=doctor_id, date=date_, available_times=slots)


@router.post(
    "/appointments", response_model=AppointmentCreated, status_code=status.HTTP_201_CREATED
)
def create_appointment(payload: AppointmentCreate, db: DbSession) -> AppointmentCreated:
    try:
        appointment = appointment_service.create_appointment(db, payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AppointmentCreated(
        public_reference=appointment.public_reference, status=appointment.status
    )


@router.get("/appointments/{public_reference}", response_model=AppointmentPublicStatus)
def get_appointment_status(public_reference: str, db: DbSession) -> AppointmentPublicStatus:
    try:
        appointment = appointment_service.get_public_status(db, public_reference)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc

    doctor = None
    if appointment.confirmed_doctor_id:
        doctor = DoctorRepository(db).get(appointment.confirmed_doctor_id)
    elif appointment.doctor_id:
        doctor = DoctorRepository(db).get(appointment.doctor_id)

    return AppointmentPublicStatus(
        public_reference=appointment.public_reference,
        status=appointment.status,
        doctor=DoctorPublic.model_validate(doctor) if doctor else None,
        confirmed_date=appointment.confirmed_date,
        confirmed_time=appointment.confirmed_time,
        proposed_date=appointment.proposed_date,
        proposed_time=appointment.proposed_time,
    )


@router.post("/appointments/{public_reference}/confirm-proposed-slot", response_model=AppointmentPublicStatus)
def confirm_proposed_slot(
    public_reference: str, payload: ConfirmProposedSlotRequest, db: DbSession
) -> AppointmentPublicStatus:
    try:
        appointment = appointment_service.confirm_proposed_slot(
            db, public_reference=public_reference, token=payload.token
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc
    except (InvalidTransitionError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    doctor = DoctorRepository(db).get(appointment.confirmed_doctor_id) if appointment.confirmed_doctor_id else None
    return AppointmentPublicStatus(
        public_reference=appointment.public_reference,
        status=appointment.status,
        doctor=DoctorPublic.model_validate(doctor) if doctor else None,
        confirmed_date=appointment.confirmed_date,
        confirmed_time=appointment.confirmed_time,
        proposed_date=appointment.proposed_date,
        proposed_time=appointment.proposed_time,
    )
