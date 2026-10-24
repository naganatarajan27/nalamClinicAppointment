import logging

from app.core.config import Settings, get_settings
from app.integrations.whatsapp.base import WhatsAppNotificationService
from app.integrations.whatsapp.cloud_api_adapter import WhatsAppCloudApiAdapter
from app.integrations.whatsapp.mock_adapter import MockWhatsAppAdapter

logger = logging.getLogger("nalam.whatsapp")


def get_whatsapp_adapter(settings: Settings | None = None) -> WhatsAppNotificationService:
    settings = settings or get_settings()
    if settings.whatsapp_provider == "cloud_api":
        return WhatsAppCloudApiAdapter(settings)

    logger.info("Using MOCK WhatsApp adapter - no real messages will be sent.")
    return MockWhatsAppAdapter()
