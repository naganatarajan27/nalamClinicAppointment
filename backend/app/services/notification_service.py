from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.email.base import EmailNotificationService
from app.integrations.whatsapp.base import WhatsAppNotificationService
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import NotificationChannel, NotificationStatus, NotificationType
from app.models.notification_attempt import NotificationAttempt
from app.repositories.notification_repository import NotificationRepository


def _proposed_slot_confirmation_link(appointment: Appointment) -> str:
    frontend_origin = get_settings().frontend_origin.rstrip("/")
    return (
        f"{frontend_origin}/confirm/{appointment.public_reference}"
        f"?token={appointment.proposed_slot_token}"
    )


class NotificationService:
    def __init__(
        self,
        db: Session,
        whatsapp: WhatsAppNotificationService,
        email: EmailNotificationService | None = None,
    ) -> None:
        self.db = db
        self.whatsapp = whatsapp
        self.email = email
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

    def _send_whatsapp_confirmation(self, appointment: Appointment, doctor: Doctor):
        return self.whatsapp.send_confirmation(
            whatsapp_number=appointment.whatsapp_number,
            patient_name=appointment.patient_name,
            doctor_name=doctor.display_name,
            appointment_date=appointment.confirmed_date,
            appointment_time=appointment.confirmed_time,
            reference_number=appointment.public_reference,
        )

    def _send_whatsapp_alternate_proposal(self, appointment: Appointment, doctor: Doctor):
        return self.whatsapp.send_alternate_proposal(
            whatsapp_number=appointment.whatsapp_number,
            patient_name=appointment.patient_name,
            doctor_name=doctor.display_name,
            proposed_date=appointment.proposed_date,
            proposed_time=appointment.proposed_time,
            reference_number=appointment.public_reference,
            next_step=f"confirm at {_proposed_slot_confirmation_link(appointment)}, or call the clinic",
        )

    def _send_email_confirmation(self, appointment: Appointment, doctor: Doctor):
        assert self.email is not None
        return self.email.send_confirmation(
            to_email=appointment.email,
            patient_name=appointment.patient_name,
            doctor_name=doctor.display_name,
            appointment_date=appointment.confirmed_date,
            appointment_time=appointment.confirmed_time,
            reference_number=appointment.public_reference,
        )

    def send_confirmation(self, appointment: Appointment, doctor: Doctor) -> list[NotificationAttempt]:
        """Sends the WhatsApp confirmation, plus an email confirmation if the
        patient provided an email address. Returns one attempt per channel sent.
        """
        attempts = []

        whatsapp_attempt = self.repo.create(
            NotificationAttempt(
                appointment_id=appointment.id,
                channel=NotificationChannel.WHATSAPP,
                notification_type=NotificationType.CONFIRMATION,
                status=NotificationStatus.QUEUED,
            )
        )
        attempts.append(self._apply_result(whatsapp_attempt, self._send_whatsapp_confirmation(appointment, doctor)))

        if appointment.email and self.email is not None:
            email_attempt = self.repo.create(
                NotificationAttempt(
                    appointment_id=appointment.id,
                    channel=NotificationChannel.EMAIL,
                    notification_type=NotificationType.CONFIRMATION,
                    status=NotificationStatus.QUEUED,
                )
            )
            attempts.append(self._apply_result(email_attempt, self._send_email_confirmation(appointment, doctor)))

        return attempts

    def send_alternate_proposal(self, appointment: Appointment, doctor: Doctor) -> NotificationAttempt:
        attempt = self.repo.create(
            NotificationAttempt(
                appointment_id=appointment.id,
                channel=NotificationChannel.WHATSAPP,
                notification_type=NotificationType.ALTERNATE_PROPOSAL,
                status=NotificationStatus.QUEUED,
            )
        )
        return self._apply_result(attempt, self._send_whatsapp_alternate_proposal(appointment, doctor))

    def retry(self, attempt: NotificationAttempt, appointment: Appointment, doctor: Doctor) -> NotificationAttempt:
        if attempt.channel == NotificationChannel.EMAIL:
            if self.email is None:
                raise ValueError("Email adapter is not configured.")
            result = self._send_email_confirmation(appointment, doctor)
        elif attempt.notification_type == NotificationType.CONFIRMATION:
            result = self._send_whatsapp_confirmation(appointment, doctor)
        else:
            result = self._send_whatsapp_alternate_proposal(appointment, doctor)
        return self._apply_result(attempt, result)
