import logging
import uuid
from datetime import date, time

from app.integrations.whatsapp.base import WhatsAppNotificationService, WhatsAppSendResult
from app.models.enums import NotificationStatus

logger = logging.getLogger("nalam.whatsapp.mock")


class MockWhatsAppAdapter(WhatsAppNotificationService):
    """Logs messages instead of calling a real provider.

    Used automatically when WHATSAPP_PROVIDER=mock (the default), e.g. in
    local development and tests when no provider credentials are
    configured. Never claims a message was actually delivered.
    """

    def send_confirmation(
        self,
        *,
        whatsapp_number: str,
        patient_name: str,
        doctor_name: str,
        appointment_date: date,
        appointment_time: time,
        reference_number: str,
    ) -> WhatsAppSendResult:
        message_id = f"mock-{uuid.uuid4()}"
        logger.info(
            "MOCK WhatsApp confirmation NOT actually sent to %s: patient=%s doctor=%s "
            "date=%s time=%s ref=%s (mock_message_id=%s)",
            whatsapp_number,
            patient_name,
            doctor_name,
            appointment_date,
            appointment_time,
            reference_number,
            message_id,
        )
        return WhatsAppSendResult(status=NotificationStatus.SENT, provider_message_id=message_id)

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
    ) -> WhatsAppSendResult:
        message_id = f"mock-{uuid.uuid4()}"
        logger.info(
            "MOCK WhatsApp alternate-slot proposal NOT actually sent to %s: patient=%s "
            "doctor=%s date=%s time=%s ref=%s next_step=%s (mock_message_id=%s)",
            whatsapp_number,
            patient_name,
            doctor_name,
            proposed_date,
            proposed_time,
            reference_number,
            next_step,
            message_id,
        )
        return WhatsAppSendResult(status=NotificationStatus.SENT, provider_message_id=message_id)
