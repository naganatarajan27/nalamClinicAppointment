from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, time

from app.models.enums import NotificationStatus


@dataclass
class WhatsAppSendResult:
    status: NotificationStatus
    provider_message_id: str | None = None
    error_summary: str | None = None


class WhatsAppNotificationService(ABC):
    """Abstraction over a WhatsApp Business provider.

    Implementations must never raise for expected provider failures -
    they should return a WhatsAppSendResult with status=FAILED and a
    sanitized error_summary so callers can persist the notification
    attempt without the request failing.
    """

    @abstractmethod
    def send_confirmation(
        self,
        *,
        whatsapp_number: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: date,
        appointment_time: time,
        reference_number: str,
    ) -> WhatsAppSendResult: ...

    @abstractmethod
    def send_alternate_proposal(
        self,
        *,
        whatsapp_number: str,
        patient_name: str,
        doctor_name: str,
        proposed_date: date,
        proposed_time: time,
        reference_number: str,
        next_step: str,
    ) -> WhatsAppSendResult: ...
