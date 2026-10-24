import logging
import uuid
from datetime import date, time

from app.integrations.email.base import EmailNotificationService, EmailSendResult
from app.models.enums import NotificationStatus

logger = logging.getLogger("nalam.email.mock")


class MockEmailAdapter(EmailNotificationService):
    """Logs messages instead of calling a real email provider.

    Used automatically when EMAIL_PROVIDER=mock (the default), e.g. in local
    development and tests when no SMTP credentials are configured. Never
    claims an email was actually delivered.
    """

    def send_confirmation(
        self,
        *,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: date,
        appointment_time: time,
        reference_number: str,
    ) -> EmailSendResult:
        message_id = f"mock-{uuid.uuid4()}"
        logger.info(
            "MOCK confirmation email NOT actually sent to %s: patient=%s doctor=%s date=%s "
            "time=%s ref=%s (mock_message_id=%s)",
            to_email,
            patient_name,
            doctor_name,
            appointment_date,
            appointment_time,
            reference_number,
            message_id,
        )
        return EmailSendResult(status=NotificationStatus.SENT, provider_message_id=message_id)
