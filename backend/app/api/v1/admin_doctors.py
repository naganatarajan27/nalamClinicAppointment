import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentAdmin, DbSession, require_csrf
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import DoctorAdmin, DoctorCreate, DoctorUpdate
from app.services import doctor_service

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
