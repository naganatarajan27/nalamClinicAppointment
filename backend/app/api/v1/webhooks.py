import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.api.deps import AppSettings, DbSession
from app.models.enums import NotificationStatus
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger("nalam.whatsapp.webhook")

router = APIRouter(prefix="/webhooks/whatsapp", tags=["webhooks"])

_PROVIDER_STATUS_MAP = {
    "sent": NotificationStatus.SENT,
    "delivered": NotificationStatus.DELIVERED,
    "read": NotificationStatus.DELIVERED,
    "failed": NotificationStatus.FAILED,
}


@router.get("")
def verify_webhook(
    settings: AppSettings,
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    """Meta's webhook verification handshake.

    See https://developers.facebook.com/docs/graph-api/webhooks/getting-started
    """
    if hub_mode != "subscribe" or hub_verify_token != settings.whatsapp_webhook_verify_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verify token.")
    return Response(content=hub_challenge, media_type="text/plain")


@router.post("", status_code=status.HTTP_200_OK)
async def receive_status_update(request: Request, db: DbSession) -> dict[str, str]:
    """Receives delivery-status callbacks for previously sent messages.

    Never trust this payload for anything beyond updating notification
    status - it is unauthenticated beyond the verify-token handshake used
    at subscription time, as documented by Meta for Cloud API webhooks.
    """
    body = await request.json()
    repo = NotificationRepository(db)

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for status_update in value.get("statuses", []):
                provider_message_id = status_update.get("id")
                provider_status = status_update.get("status")
                if not provider_message_id or provider_status not in _PROVIDER_STATUS_MAP:
                    continue

                attempt = repo.get_by_provider_message_id(provider_message_id)
                if attempt is None:
                    logger.info("Webhook status for unknown message id %s", provider_message_id)
                    continue

                new_status = _PROVIDER_STATUS_MAP[provider_status]
                # Never downgrade a terminal DELIVERED status back to SENT.
                if attempt.status == NotificationStatus.DELIVERED and new_status == NotificationStatus.SENT:
                    continue
                attempt.status = new_status
                if new_status == NotificationStatus.DELIVERED and attempt.sent_at is None:
                    attempt.sent_at = datetime.now(UTC)

    db.commit()
    return {"status": "received"}
