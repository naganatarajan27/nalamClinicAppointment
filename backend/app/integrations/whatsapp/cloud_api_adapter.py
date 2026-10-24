import logging
from datetime import date, time

import httpx

from app.core.config import Settings
from app.integrations.whatsapp.base import WhatsAppNotificationService, WhatsAppSendResult
from app.models.enums import NotificationStatus

logger = logging.getLogger("nalam.whatsapp.cloud_api")

GRAPH_BASE_URL = "https://graph.facebook.com"


class WhatsAppCloudApiAdapter(WhatsAppNotificationService):
    """Sends messages through the official WhatsApp Business Cloud API.

    Requires an approved message template for each notification type,
    configured via WHATSAPP_TEMPLATE_CONFIRMATION / WHATSAPP_TEMPLATE_ALTERNATE_SLOT,
    plus WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID. See docs/setup.md.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _send_template(self, *, to: str, template_name: str, parameters: list[str]) -> WhatsAppSendResult:
        if not (self._settings.whatsapp_access_token and self._settings.whatsapp_phone_number_id):
            return WhatsAppSendResult(
                status=NotificationStatus.FAILED,
                error_summary="WhatsApp Cloud API credentials are not configured.",
            )
        if not template_name:
            return WhatsAppSendResult(
                status=NotificationStatus.FAILED,
                error_summary="No approved WhatsApp template configured for this notification type.",
            )

        url = (
            f"{GRAPH_BASE_URL}/{self._settings.whatsapp_api_version}/"
            f"{self._settings.whatsapp_phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in parameters],
                    }
                ],
            },
        }
        headers = {"Authorization": f"Bearer {self._settings.whatsapp_access_token}"}

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        except httpx.HTTPError as exc:
            logger.warning("WhatsApp Cloud API request failed: %s", exc.__class__.__name__)
            return WhatsAppSendResult(
                status=NotificationStatus.FAILED,
                error_summary=f"Network error contacting WhatsApp provider ({exc.__class__.__name__}).",
            )

        if response.status_code >= 400:
            logger.warning("WhatsApp Cloud API returned status %s", response.status_code)
            return WhatsAppSendResult(
                status=NotificationStatus.FAILED,
                error_summary=f"WhatsApp provider rejected the message (HTTP {response.status_code}).",
            )

        data = response.json()
        message_id = None
        messages = data.get("messages") or []
        if messages:
            message_id = messages[0].get("id")

        return WhatsAppSendResult(status=NotificationStatus.SENT, provider_message_id=message_id)

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
        return self._send_template(
            to=whatsapp_number,
            template_name=self._settings.whatsapp_template_confirmation,
            parameters=[
                patient_name,
                doctor_name,
                appointment_date.isoformat(),
                appointment_time.strftime("%H:%M"),
                reference_number,
            ],
        )

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
        return self._send_template(
            to=whatsapp_number,
            template_name=self._settings.whatsapp_template_alternate_slot,
            parameters=[
                patient_name,
                proposed_date.isoformat(),
                proposed_time.strftime("%H:%M"),
                doctor_name,
                next_step,
                reference_number,
            ],
        )
