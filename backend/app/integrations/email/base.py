from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, time

from app.models.enums import NotificationStatus


@dataclass
class EmailSendResult:
    status: NotificationStatus
    provider_message_id: str | None = None
    error_summary: str | None = None


class EmailNotificationService(ABC):
    """Abstraction over an email provider, mirroring WhatsAppNotificationService.

    Implementations must never raise for expected provider failures - they
    should return an EmailSendResult with status=FAILED and a sanitized
    error_summary so callers can persist the notification attempt without
    the request failing.
    """

    @abstractmethod
    def send_confirmation(
        self,
        *,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: date,
        appointment_time: time,
        reference_number: str,
    ) -> EmailSendResult: ...
