import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentAdmin, DbSession, require_csrf
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import DoctorAdmin, DoctorCreate, DoctorUpdate
from app.schemas.doctor_availability import (
    DoctorAvailabilityCreate,
    DoctorAvailabilityOut,
    DoctorAvailabilityUpdate,
)
from app.services import doctor_availability_service, doctor_service
from app.services.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/admin/doctors", tags=["admin-doctors"])


@router.get("", response_model=list[DoctorAdmin])
def list_doctors(db: DbSession, _admin: CurrentAdmin) -> list[DoctorAdmin]:
    return [DoctorAdmin.model_validate(d) for d in doctor_service.list_all_doctors(db)]


@router.post("", response_model=DoctorAdmin, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_doctor(payload: DoctorCreate, db: DbSession, _admin: CurrentAdmin) -> DoctorAdmin:
    doctor = doctor_service.create_doctor(db, payload)
    return DoctorAdmin.model_validate(doctor)


@router.patch("/{doctor_id}", response_model=DoctorAdmin, dependencies=[Depends(require_csrf)])
def update_doctor(doctor_id: uuid.UUID, payload: DoctorUpdate, db: DbSession, _admin: CurrentAdmin) -> DoctorAdmin:
    repo = DoctorRepository(db)
    doctor = repo.get(doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    if payload.display_name is not None:
        doctor.display_name = payload.display_name
    if payload.specialty is not None:
        doctor.specialty = payload.specialty
    if payload.is_active is not None:
        doctor.is_active = payload.is_active
    db.commit()
    return DoctorAdmin.model_validate(doctor)


@router.get("/{doctor_id}/availability", response_model=list[DoctorAvailabilityOut])
def list_availability(doctor_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin) -> list[DoctorAvailabilityOut]:
    try:
        windows = doctor_availability_service.list_for_doctor(db, doctor_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [DoctorAvailabilityOut.model_validate(w) for w in windows]


@router.post(
    "/{doctor_id}/availability",
    response_model=DoctorAvailabilityOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_availability(
    doctor_id: uuid.UUID, payload: DoctorAvailabilityCreate, db: DbSession, _admin: CurrentAdmin
) -> DoctorAvailabilityOut:
    try:
        window = doctor_availability_service.create(db, doctor_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DoctorAvailabilityOut.model_validate(window)


@router.patch(
    "/{doctor_id}/availability/{availability_id}",
    response_model=DoctorAvailabilityOut,
    dependencies=[Depends(require_csrf)],
)
def update_availability(
    doctor_id: uuid.UUID,
    availability_id: uuid.UUID,
    payload: DoctorAvailabilityUpdate,
    db: DbSession,
    _admin: CurrentAdmin,
) -> DoctorAvailabilityOut:
    try:
        window = doctor_availability_service.update(db, doctor_id, availability_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return DoctorAvailabilityOut.model_validate(window)


@router.delete(
    "/{doctor_id}/availability/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_availability(
    doctor_id: uuid.UUID, availability_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin
) -> None:
    try:
        doctor_availability_service.delete(db, doctor_id, availability_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
