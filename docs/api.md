# API

All endpoints are prefixed `/api/v1`. Full interactive schema (requests/responses/validation) is
served in development at `/docs` (Swagger UI) and `/openapi.json`.

## Public

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/doctors` | Active doctors available for booking. |
| GET | `/availability?doctor_id&date` | Fixed 09:00–17:00 / 30-min default slots minus already-requested ones for that doctor/date. |
| POST | `/appointments` | Creates a `PENDING` request. Returns `public_reference` + `status` only. |
| GET | `/appointments/{public_reference}` | Status lookup. Never returns symptoms, phone/WhatsApp numbers, or admin notes. |
| POST | `/appointments/{public_reference}/confirm-proposed-slot` | Patient accepts an `ALTERNATE_PROPOSED` slot using the single-use token sent over WhatsApp. |

## Admin (session cookie required; mutating requests also require the `X-CSRF-Token` header)

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/admin/auth/login` | Rate-limited per `ip:email`. Sets the session + CSRF cookies. |
| POST | `/admin/auth/logout` | Requires CSRF header. |
| GET | `/admin/auth/me` | Current admin identity. |
| GET | `/admin/appointments` | Paginated, filterable by `status`, `date_from`, `date_to`, `q` (reference/name search). |
| GET | `/admin/appointments/{id}` | Full detail, including symptoms and admin note. |
| PATCH | `/admin/appointments/{id}/accept` | Confirms the requested slot, sends the confirmation WhatsApp notification. |
| PATCH | `/admin/appointments/{id}/propose-slot` | Stores a proposed slot (never auto-confirms), sends the alternate-slot notification. |
| PATCH | `/admin/appointments/{id}/status` | Only cancel/complete transitions — see `ALLOWED_STATUS_TRANSITIONS` in `app/models/enums.py`. |
| GET | `/admin/appointments/{id}/notifications` | Notification attempt history for one appointment. |
| POST | `/admin/appointments/{id}/notifications/retry` | Re-sends the most recent notification attempt. |
| GET / POST / PATCH | `/admin/doctors` | List/create/update doctors (create/update require CSRF). |

## Webhooks

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/webhooks/whatsapp` | Meta's subscription verification handshake. |
| POST | `/webhooks/whatsapp` | Delivery-status callbacks; updates `NotificationAttempt.status`. |

## Error format

Errors are returned as `{"detail": "..."}` (or FastAPI's standard `{"detail": [...]}` field-error
list for 422 validation errors). No stack traces or internal details are ever included — unhandled
exceptions are caught in `app/main.py` and returned as a generic 500.
