import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_attempt import NotificationAttempt


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, attempt: NotificationAttempt) -> NotificationAttempt:
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def list_for_appointment(self, appointment_id: uuid.UUID) -> list[NotificationAttempt]:
        stmt = (
            select(NotificationAttempt)
            .where(NotificationAttempt.appointment_id == appointment_id)
            .order_by(NotificationAttempt.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_by_provider_message_id(self, provider_message_id: str) -> NotificationAttempt | None:
        stmt = select(NotificationAttempt).where(
            NotificationAttempt.provider_message_id == provider_message_id
        )
        return self.db.scalars(stmt).first()

    def latest_for_appointment(self, appointment_id: uuid.UUID) -> NotificationAttempt | None:
        stmt = (
            select(NotificationAttempt)
            .where(NotificationAttempt.appointment_id == appointment_id)
            .order_by(NotificationAttempt.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()
