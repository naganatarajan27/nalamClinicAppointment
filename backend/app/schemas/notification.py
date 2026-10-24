import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationChannel, NotificationStatus, NotificationType


class NotificationAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel: NotificationChannel
    notification_type: NotificationType
    status: NotificationStatus
    provider_message_id: str | None
    attempt_count: int
    last_error_summary: str | None
    created_at: datetime
    sent_at: datetime | None
