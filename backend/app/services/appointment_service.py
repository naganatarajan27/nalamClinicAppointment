import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import generate_confirmation_token, generate_public_reference
from app.integrations.email.base import EmailNotificationService
from app.integrations.whatsapp.base import WhatsAppNotificationService
from app.models.appointment import Appointment
from app.models.enums import ALLOWED_STATUS_TRANSITIONS, AppointmentStatus, NotificationType
from app.models.notification_attempt import NotificationAttempt
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.appointment import AppointmentCreate, ProposeSlotRequest
from app.services.exceptions import InvalidTransitionError, NotFoundError, ValidationError
from app.services.notification_service import NotificationService

PROPOSED_SLOT_TOKEN_TTL_DAYS = 7


def create_appointment(db: Session, payload: AppointmentCreate) -> Appointment:
    doctor_repo = DoctorRepository(db)
    doctor = doctor_repo.get(payload.doctor_id)
    if doctor is None or not doctor.is_active:
        raise ValidationError("Selected doctor is not available for booking.")

    appointment = Appointment(
        public_reference=_unique_public_reference(db),
        patient_name=payload.patient_name,
        patient_type=payload.patient_type,
        phone_number=payload.phone_number,
        whatsapp_number=payload.whatsapp_number,
        email=payload.email,
        doctor_id=payload.doctor_id,
        requested_date=payload.requested_date,
        requested_time=payload.requested_time,
        symptoms=payload.symptoms,
        status=AppointmentStatus.PENDING,
    )
    AppointmentRepository(db).create(appointment)
    db.commit()
    return appointment


def _unique_public_reference(db: Session) -> str:
    repo = AppointmentRepository(db)
    for _ in range(5):
        candidate = generate_public_reference()
        if repo.get_by_public_reference(candidate) is None:
            return candidate
    raise RuntimeError("Could not generate a unique public reference.")


def get_for_admin(db: Session, appointment_id: uuid.UUID) -> Appointment:
    appointment = AppointmentRepository(db).get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    return appointment


def get_public_status(db: Session, public_reference: str) -> Appointment:
    appointment = AppointmentRepository(db).get_by_public_reference(public_reference)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    return appointment


def search_for_admin(
    db: Session,
    *,
    status: AppointmentStatus | None,
    date_from,
    date_to,
    query: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Appointment], int]:
    return AppointmentRepository(db).search(
        status=status,
        date_from=date_from,
        date_to=date_to,
        query=query,
        page=page,
        page_size=page_size,
    )


def accept_appointment(
    db: Session,
    *,
    appointment_id: uuid.UUID,
    admin_id: uuid.UUID,
    admin_note: str | None,
    whatsapp: WhatsAppNotificationService,
    email: EmailNotificationService | None = None,
) -> tuple[Appointment, list[NotificationAttempt]]:
    appointment = get_for_admin(db, appointment_id)
    if appointment.status not in (AppointmentStatus.PENDING, AppointmentStatus.ALTERNATE_PROPOSED):
        raise InvalidTransitionError(
            f"Cannot accept an appointment with status {appointment.status.value}."
        )

    doctor_repo = DoctorRepository(db)
    doctor = doctor_repo.get(appointment.doctor_id)
    if doctor is None:
        raise ValidationError("Original doctor no longer exists.")

    appointment.confirmed_doctor_id = appointment.doctor_id
    appointment.confirmed_date = appointment.requested_date
    appointment.confirmed_time = appointment.requested_time
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.reviewed_by_admin_id = admin_id
    appointment.reviewed_at = datetime.now(UTC)
    if admin_note:
        appointment.admin_note = admin_note
    db.flush()

    notification_service = NotificationService(db, whatsapp, email)
    attempts = notification_service.send_confirmation(appointment, doctor)
    db.commit()
    return appointment, attempts


def propose_alternate_slot(
    db: Session,
    *,
    appointment_id: uuid.UUID,
    admin_id: uuid.UUID,
    payload: ProposeSlotRequest,
    whatsapp: WhatsAppNotificationService,
) -> tuple[Appointment, NotificationAttempt]:
    appointment = get_for_admin(db, appointment_id)
    if appointment.status not in (AppointmentStatus.PENDING, AppointmentStatus.ALTERNATE_PROPOSED):
        raise InvalidTransitionError(
            f"Cannot propose a new slot for an appointment with status {appointment.status.value}."
        )

    doctor_repo = DoctorRepository(db)
    proposed_doctor_id = payload.proposed_doctor_id or appointment.doctor_id
    doctor = doctor_repo.get(proposed_doctor_id)
    if doctor is None or not doctor.is_active:
        raise ValidationError("Proposed doctor is not available.")

    appointment.proposed_doctor_id = proposed_doctor_id
    appointment.proposed_date = payload.proposed_date
    appointment.proposed_time = payload.proposed_time
    appointment.proposed_slot_token = generate_confirmation_token()
    appointment.proposed_slot_token_expires_at = datetime.now(UTC) + timedelta(
        days=PROPOSED_SLOT_TOKEN_TTL_DAYS
    )
    appointment.status = AppointmentStatus.ALTERNATE_PROPOSED
    appointment.reviewed_by_admin_id = admin_id
    appointment.reviewed_at = datetime.now(UTC)
    if payload.admin_note:
        appointment.admin_note = payload.admin_note
    db.flush()

    notification_service = NotificationService(db, whatsapp)
    attempt = notification_service.send_alternate_proposal(appointment, doctor)
    db.commit()
    return appointment, attempt


def update_status(
    db: Session, *, appointment_id: uuid.UUID, admin_id: uuid.UUID, new_status: AppointmentStatus
) -> Appointment:
    appointment = get_for_admin(db, appointment_id)
    allowed = ALLOWED_STATUS_TRANSITIONS.get(appointment.status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot move an appointment from {appointment.status.value} to {new_status.value}."
        )

    appointment.status = new_status
    appointment.reviewed_by_admin_id = admin_id
    appointment.reviewed_at = datetime.now(UTC)
    db.commit()
    return appointment


def retry_notification(
    db: Session,
    *,
    appointment_id: uuid.UUID,
    notification_id: uuid.UUID,
    whatsapp: WhatsAppNotificationService,
    email: EmailNotificationService | None = None,
) -> NotificationAttempt:
    appointment = get_for_admin(db, appointment_id)
    attempt = NotificationRepository(db).get(notification_id)
    if attempt is None or attempt.appointment_id != appointment.id:
        raise NotFoundError("Notification attempt not found.")

    doctor_id = (
        appointment.confirmed_doctor_id
        if attempt.notification_type == NotificationType.CONFIRMATION
        else appointment.proposed_doctor_id
    )
    doctor = DoctorRepository(db).get(doctor_id) if doctor_id else None
    if doctor is None:
        raise ValidationError("No doctor associated with this notification.")

    notification_service = NotificationService(db, whatsapp, email)
    notification_service.retry(attempt, appointment, doctor)
    db.commit()
    return attempt


def confirm_proposed_slot(db: Session, *, public_reference: str, token: str) -> Appointment:
    appointment = get_public_status(db, public_reference)
    if appointment.status != AppointmentStatus.ALTERNATE_PROPOSED:
        raise InvalidTransitionError("This appointment has no pending proposed slot.")
    if not appointment.proposed_slot_token or appointment.proposed_slot_token != token:
        raise ValidationError("Invalid or expired confirmation link.")
    expires_at = appointment.proposed_slot_token_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        # SQLite (used in tests) does not preserve tzinfo on DateTime(timezone=True)
        # columns; values written here are always UTC.
        expires_at = expires_at.replace(tzinfo=UTC)
    if not expires_at or expires_at < datetime.now(UTC):
        raise ValidationError("Invalid or expired confirmation link.")

    appointment.confirmed_doctor_id = appointment.proposed_doctor_id
    appointment.confirmed_date = appointment.proposed_date
    appointment.confirmed_time = appointment.proposed_time
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.proposed_slot_token = None
    appointment.proposed_slot_token_expires_at = None
    db.commit()
    return appointment
