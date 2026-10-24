from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.integrations.whatsapp.base import WhatsAppNotificationService
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import NotificationStatus, NotificationType
from app.models.notification_attempt import NotificationAttempt
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, db: Session, whatsapp: WhatsAppNotificationService) -> None:
        self.db = db
        self.whatsapp = whatsapp
        self.repo = NotificationRepository(db)

    def _apply_result(self, attempt: NotificationAttempt, result) -> NotificationAttempt:
        attempt.attempt_count += 1
        attempt.status = result.status
        attempt.provider_message_id = result.provider_message_id
        attempt.last_error_summary = result.error_summary
        if result.status in (NotificationStatus.SENT, NotificationStatus.DELIVERED):
            attempt.sent_at = datetime.now(UTC)
        self.db.flush()
        return attempt

    def send_confirmation(self, appointment: Appointment, doctor: Doctor) -> NotificationAttempt:
        attempt = self.repo.create(
            NotificationAttempt(
                appointment_id=appointment.id,
                notification_type=NotificationType.CONFIRMATION,
                status=NotificationStatus.QUEUED,
            )
        )
        result = self.whatsapp.send_confirmation(
            whatsapp_number=appointment.whatsapp_number,
            patient_name=appointment.patient_name,
            doctor_name=doctor.display_name,
            appointment_date=appointment.confirmed_date,
            appointment_time=appointment.confirmed_time,
            reference_number=appointment.public_reference,
        )
        return self._apply_result(attempt, result)

    def send_alternate_proposal(
        self, appointment: Appointment, doctor: Doctor, *, next_step: str
    ) -> NotificationAttempt:
        attempt = self.repo.create(
            NotificationAttempt(
                appointment_id=appointment.id,
                notification_type=NotificationType.ALTERNATE_PROPOSAL,
                status=NotificationStatus.QUEUED,
            )
        )
        result = self.whatsapp.send_alternate_proposal(
            whatsapp_number=appointment.whatsapp_number,
            patient_name=appointment.patient_name,
            doctor_name=doctor.display_name,
            proposed_date=appointment.proposed_date,
            proposed_time=appointment.proposed_time,
            reference_number=appointment.public_reference,
            next_step=next_step,
        )
        return self._apply_result(attempt, result)

    def retry_latest(self, appointment: Appointment, doctor: Doctor) -> NotificationAttempt | None:
        latest = self.repo.latest_for_appointment(appointment.id)
        if latest is None:
            return None

        if latest.notification_type == NotificationType.CONFIRMATION:
            result = self.whatsapp.send_confirmation(
                whatsapp_number=appointment.whatsapp_number,
                patient_name=appointment.patient_name,
                doctor_name=doctor.display_name,
                appointment_date=appointment.confirmed_date,
                appointment_time=appointment.confirmed_time,
                reference_number=appointment.public_reference,
            )
        else:
            result = self.whatsapp.send_alternate_proposal(
                whatsapp_number=appointment.whatsapp_number,
                patient_name=appointment.patient_name,
                doctor_name=doctor.display_name,
                proposed_date=appointment.proposed_date,
                proposed_time=appointment.proposed_time,
                reference_number=appointment.public_reference,
                next_step="contact the clinic to confirm",
            )
        return self._apply_result(latest, result)
