import logging

from app.core.config import Settings, get_settings
from app.integrations.email.base import EmailNotificationService
from app.integrations.email.mock_adapter import MockEmailAdapter
from app.integrations.email.smtp_adapter import SmtpEmailAdapter

logger = logging.getLogger("nalam.email")


def get_email_adapter(settings: Settings | None = None) -> EmailNotificationService:
    settings = settings or get_settings()
    if settings.email_provider == "smtp":
        return SmtpEmailAdapter(settings)

    logger.info("Using MOCK email adapter - no real emails will be sent.")
    return MockEmailAdapter()
