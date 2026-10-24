import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import CurrentAdmin, DbSession, get_whatsapp_service, require_csrf
from app.integrations.whatsapp.base import WhatsAppNotificationService
from app.models.enums import AppointmentStatus
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.appointment import (
    AcceptAppointmentRequest,
    AppointmentAdminDetail,
    AppointmentAdminListItem,
    ProposeSlotRequest,
    StatusUpdateRequest,
)
from app.schemas.doctor import DoctorPublic
from app.schemas.notification import NotificationAttemptOut
from app.services import appointment_service
from app.services.exceptions import InvalidTransitionError, NotFoundError, ValidationError
from app.services.masking import mask_phone_number

router = APIRouter(prefix="/admin/appointments", tags=["admin-appointments"], dependencies=[Depends(require_csrf)])

read_router = APIRouter(prefix="/admin/appointments", tags=["admin-appointments"])


class AppointmentListResponse(BaseModel):
    items: list[AppointmentAdminListItem]
    total: int
    page: int
    page_size: int


def _to_list_item(db, appointment) -> AppointmentAdminListItem:
    doctor = DoctorRepository(db).get(appointment.doctor_id)
    latest = NotificationRepository(db).latest_for_appointment(appointment.id)
    return AppointmentAdminListItem(
        id=appointment.id,
        public_reference=appointment.public_reference,
        patient_name=appointment.patient_name,
        patient_type=appointment.patient_type,
        phone_number=appointment.phone_number,
        whatsapp_number_masked=mask_phone_number(appointment.whatsapp_number),
        doctor=DoctorPublic.model_validate(doctor) if doctor else None,
        requested_date=appointment.requested_date,
        requested_time=appointment.requested_time,
        status=appointment.status,
        created_at=appointment.created_at,
        latest_notification_status=latest.status.value if latest else None,
    )


def _to_detail(db, appointment) -> AppointmentAdminDetail:
    doctor_repo = DoctorRepository(db)
    doctor = doctor_repo.get(appointment.doctor_id)
    confirmed_doctor = doctor_repo.get(appointment.confirmed_doctor_id) if appointment.confirmed_doctor_id else None
    proposed_doctor = doctor_repo.get(appointment.proposed_doctor_id) if appointment.proposed_doctor_id else None
    return AppointmentAdminDetail(
        id=appointment.id,
        public_reference=appointment.public_reference,
        patient_name=appointment.patient_name,
        patient_type=appointment.patient_type,
        phone_number=appointment.phone_number,
        whatsapp_number=appointment.whatsapp_number,
        doctor=DoctorPublic.model_validate(doctor) if doctor else None,
        requested_date=appointment.requested_date,
        requested_time=appointment.requested_time,
        confirmed_doctor=DoctorPublic.model_validate(confirmed_doctor) if confirmed_doctor else None,
        confirmed_date=appointment.confirmed_date,
        confirmed_time=appointment.confirmed_time,
        proposed_doctor=DoctorPublic.model_validate(proposed_doctor) if proposed_doctor else None,
        proposed_date=appointment.proposed_date,
        proposed_time=appointment.proposed_time,
        symptoms=appointment.symptoms,
        status=appointment.status,
        admin_note=appointment.admin_note,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        reviewed_by_admin_id=appointment.reviewed_by_admin_id,
        reviewed_at=appointment.reviewed_at,
    )


@read_router.get("", response_model=AppointmentListResponse)
def list_appointments(
    db: DbSession,
    _admin: CurrentAdmin,
    status_: AppointmentStatus | None = Query(default=None, alias="status"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    q: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AppointmentListResponse:
    items, total = appointment_service.search_for_admin(
        db, status=status_, date_from=date_from, date_to=date_to, query=q, page=page, page_size=page_size
    )
    return AppointmentListResponse(
        items=[_to_list_item(db, a) for a in items], total=total, page=page, page_size=page_size
    )


@read_router.get("/{appointment_id}", response_model=AppointmentAdminDetail)
def get_appointment(appointment_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin) -> AppointmentAdminDetail:
    try:
        appointment = appointment_service.get_for_admin(db, appointment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc
    return _to_detail(db, appointment)


@router.patch("/{appointment_id}/accept", response_model=AppointmentAdminDetail)
def accept_appointment(
    appointment_id: uuid.UUID,
    payload: AcceptAppointmentRequest,
    db: DbSession,
    admin: CurrentAdmin,
    whatsapp: WhatsAppNotificationService = Depends(get_whatsapp_service),
) -> AppointmentAdminDetail:
    try:
        appointment, _attempt = appointment_service.accept_appointment(
            db,
            appointment_id=appointment_id,
            admin_id=admin.id,
            admin_note=payload.admin_note,
            whatsapp=whatsapp,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc
    except (InvalidTransitionError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_detail(db, appointment)


@router.patch("/{appointment_id}/propose-slot", response_model=AppointmentAdminDetail)
def propose_slot(
    appointment_id: uuid.UUID,
    payload: ProposeSlotRequest,
    db: DbSession,
    admin: CurrentAdmin,
    whatsapp: WhatsAppNotificationService = Depends(get_whatsapp_service),
) -> AppointmentAdminDetail:
    try:
        appointment, _attempt = appointment_service.propose_alternate_slot(
            db, appointment_id=appointment_id, admin_id=admin.id, payload=payload, whatsapp=whatsapp
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc
    except (InvalidTransitionError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_detail(db, appointment)


@router.patch("/{appointment_id}/status", response_model=AppointmentAdminDetail)
def set_status(
    appointment_id: uuid.UUID, payload: StatusUpdateRequest, db: DbSession, admin: CurrentAdmin
) -> AppointmentAdminDetail:
    try:
        appointment = appointment_service.update_status(
            db, appointment_id=appointment_id, admin_id=admin.id, new_status=payload.status
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_detail(db, appointment)


@router.post("/{appointment_id}/notifications/retry", response_model=NotificationAttemptOut)
def retry_notification(
    appointment_id: uuid.UUID,
    db: DbSession,
    _admin: CurrentAdmin,
    whatsapp: WhatsAppNotificationService = Depends(get_whatsapp_service),
) -> NotificationAttemptOut:
    try:
        attempt = appointment_service.retry_notification(db, appointment_id=appointment_id, whatsapp=whatsapp)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return NotificationAttemptOut.model_validate(attempt)


@read_router.get("/{appointment_id}/notifications", response_model=list[NotificationAttemptOut])
def list_notifications(appointment_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin) -> list[NotificationAttemptOut]:
    try:
        appointment_service.get_for_admin(db, appointment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.") from exc
    attempts = NotificationRepository(db).list_for_appointment(appointment_id)
    return [NotificationAttemptOut.model_validate(a) for a in attempts]
