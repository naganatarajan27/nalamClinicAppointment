import logging
import smtplib
import uuid
from datetime import date, time
from email.message import EmailMessage

from app.core.config import Settings
from app.integrations.email.base import EmailNotificationService, EmailSendResult
from app.models.enums import NotificationStatus

logger = logging.getLogger("nalam.email.smtp")


class SmtpEmailAdapter(EmailNotificationService):
    """Sends confirmation emails over SMTP.

    Works with Gmail SMTP, SendGrid/Mailgun/SES SMTP relays, or any standard
    SMTP server. Configure via SMTP_HOST, SMTP_PORT, SMTP_USERNAME,
    SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_USE_TLS. See docs/setup.md.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

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
        if not (self._settings.smtp_host and self._settings.smtp_from_email):
            return EmailSendResult(
                status=NotificationStatus.FAILED,
                error_summary="SMTP is not configured (SMTP_HOST / SMTP_FROM_EMAIL missing).",
            )

        message = EmailMessage()
        message["Subject"] = f"Your Nalam Clinic appointment is confirmed - {reference_number}"
        message["From"] = self._settings.smtp_from_email
        message["To"] = to_email
        message.set_content(
            "Hello {name},\n\n"
            "Your appointment at Nalam Clinic is confirmed.\n\n"
            "Doctor: {doctor}\n"
            "Date: {date}\n"
            "Time: {time}\n"
            "Reference: {ref}\n\n"
            "Please contact the clinic if you need to make a change.\n".format(
                name=patient_name,
                doctor=doctor_name,
                date=appointment_date.isoformat(),
                time=appointment_time.strftime("%H:%M"),
                ref=reference_number,
            )
        )
        message_id = f"{uuid.uuid4()}@nalamclinic"
        message["Message-ID"] = f"<{message_id}>"

        try:
            with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=10) as client:
                if self._settings.smtp_use_tls:
                    client.starttls()
                if self._settings.smtp_username:
                    client.login(self._settings.smtp_username, self._settings.smtp_password)
                client.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            logger.warning("SMTP send failed: %s", exc.__class__.__name__)
            return EmailSendResult(
                status=NotificationStatus.FAILED,
                error_summary=f"Email provider error ({exc.__class__.__name__}).",
            )

        return EmailSendResult(status=NotificationStatus.SENT, provider_message_id=message_id)
