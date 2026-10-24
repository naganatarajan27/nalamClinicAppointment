# Architecture

## Layers (backend)

`backend/app/` is layered so each layer only talks to the one below it:

- **`api/v1/`** — FastAPI routers. Converts HTTP <-> Pydantic schemas, maps domain exceptions
  (`app/services/exceptions.py`) to HTTP status codes, and enforces auth/CSRF via
  `app/api/deps.py`. Never touches the ORM directly.
- **`services/`** — business logic and transaction boundaries (`appointment_service.py`,
  `auth_service.py`, `notification_service.py`, `availability_service.py`). Owns status-transition
  rules (`app/models/enums.py:ALLOWED_STATUS_TRANSITIONS`) and orchestrates
  repositories + the WhatsApp integration.
- **`repositories/`** — SQLAlchemy queries only, one per aggregate (`Admin`, `Doctor`,
  `DoctorAvailability`, `Appointment`, `NotificationAttempt`). No business rules here.
- **`models/`** — SQLAlchemy ORM models and the shared enums/status-transition map.
- **`schemas/`** — Pydantic request/response models. API routes never return ORM objects
  directly (see `AppointmentAdminDetail` vs. the public `AppointmentPublicStatus`, which
  deliberately excludes symptoms/contact fields).
- **`integrations/whatsapp/`** and **`integrations/email/`** — each is an abstract
  `*NotificationService` interface with a mock adapter (default; logs instead of sending) and a
  real one (`WhatsAppCloudApiAdapter` / `SmtpEmailAdapter`), selected by `WHATSAPP_PROVIDER` /
  `EMAIL_PROVIDER` via each integration's `factory.py`. This is what makes sends mockable in
  tests without touching the network.

## Appointment lifecycle

`Appointment.status` is a small state machine (`app/models/enums.py`):

```
PENDING ──accept──────────────► CONFIRMED
PENDING ──propose-slot────────► ALTERNATE_PROPOSED
ALTERNATE_PROPOSED ──accept───► CONFIRMED            (admin confirms directly)
ALTERNATE_PROPOSED ──patient───► CONFIRMED            (patient uses the proposed-slot token)
ALTERNATE_PROPOSED ──propose───► ALTERNATE_PROPOSED   (admin revises the proposal)
PENDING / CONFIRMED / ALTERNATE_PROPOSED ──cancel───► CANCELLED
CONFIRMED ──complete──────────► COMPLETED
```

`accept` and `propose-slot` have dedicated service functions
(`accept_appointment`, `propose_alternate_slot`) that also create and send a
`NotificationAttempt`. The generic `PATCH /admin/appointments/{id}/status` endpoint only allows
the remaining transitions (cancel/complete), validated against
`ALLOWED_STATUS_TRANSITIONS` — it cannot be used to confirm an appointment, so a client can't
bypass the notification step.

Proposing a slot never marks the appointment confirmed: it stores `proposed_*` fields plus a
random, single-use, expiring `proposed_slot_token` (7-day TTL). The patient-facing
`POST /appointments/{public_reference}/confirm-proposed-slot` endpoint is the only way a patient
can move `ALTERNATE_PROPOSED` → `CONFIRMED` themselves; an admin can also do it via `accept`.

## Notifications

Accepting an appointment always sends a WhatsApp confirmation, plus an email confirmation if the
patient gave an email address — each is its own `NotificationAttempt` row
(`channel` = `WHATSAPP` / `EMAIL`), sent synchronously in the same request (see
`NotificationService` in `app/services/notification_service.py`). Proposing a slot only sends
WhatsApp (the spec's alternate-slot flow is WhatsApp-only). Retrying targets one specific
attempt by id (`POST /admin/appointments/{id}/notifications/{notification_id}/retry`) and re-sends
through that *same* row (`attempt_count` increments) rather than creating a new one, so a failed
WhatsApp send and a failed email send can be retried independently and each stays one history
entry rather than a growing list. The `/webhooks/whatsapp` endpoint (`app/api/v1/webhooks.py`)
updates a `NotificationAttempt` to `DELIVERED` from Meta's delivery-status callbacks, matched by
`provider_message_id`; it never downgrades a `DELIVERED` status back to `SENT`.

## Doctor availability

`DoctorAvailability` rows are a clinic-configured weekly recurring schedule per doctor
(`day_of_week` 0=Monday..6=Sunday, `start_time`, `end_time`, `slot_duration_minutes`), managed by
admins via `/admin/doctors/{id}/availability` (`app/services/doctor_availability_service.py`).
`availability_service.list_available_slots` expands the matching weekday's active windows into
concrete time slots for the requested date, then subtracts already-requested/booked times (and,
for today, past times) — this is what the public `/availability` endpoint and the booking form's
time dropdown use. A doctor with no configured window for that weekday simply has no slots; the
booking form still lets a patient type a manual time as a request in that case.

## Auth

Admin sessions are a signed, timestamped cookie (`itsdangerous`, not a sessions table) —
`app/core/security.py:create_session_token` / `read_session_token`. CSRF protection is a
double-submit cookie: login also sets a non-`HttpOnly` `nalam_csrf_token` cookie, and every
mutating admin request must echo it back in the `X-CSRF-Token` header
(`app/api/deps.py:require_csrf`). Login attempts are rate-limited per `ip:email` key
(`app/core/rate_limit.py`) — in-memory and per-process, documented as a known limitation for
multi-instance deployments.

## Frontend

`frontend/src/` mirrors the backend's intent: `api/` holds two thin fetch wrappers
(`publicApi.ts`, `adminApi.ts`) built on a shared `client.ts` that injects the CSRF header on
every non-GET request and normalizes error messages. `features/booking`, `features/admin-auth`,
`features/admin-appointments`, and `features/admin-doctors` hold the independent user flows;
`pages/` are thin route-level compositions of those features plus the shared
`SiteHeader`/`components/`. `AuthContext` (`features/admin-auth/`) holds the signed-in admin and
is the single source of truth `RequireAuth` uses to protect `/admin/*` routes.

The booking form (`features/booking/BookingForm.tsx`) collects one mobile number plus a "WhatsApp
number is the same as my mobile number" checkbox (default checked) that conditionally reveals a
second number field, and an optional email field — mirroring `AppointmentCreate`'s
`phone_number`/`whatsapp_number`/`email` fields on the backend.

`pages/ConfirmSlotPage.tsx` (route `/confirm/:reference?token=...`) is the patient-facing page for
the proposed-slot token described above — it's the link sent in the alternate-slot WhatsApp
message (built from `FRONTEND_ORIGIN` in `notification_service._proposed_slot_confirmation_link`),
not just a backend-only endpoint.

`pages/AdminDoctorsPage.tsx` (route `/admin/doctors`) hosts `features/admin-doctors/DoctorsManager`
(add/activate/deactivate doctors) and, per doctor, `DoctorAvailabilityPanel` (add/enable/disable/
remove weekly availability windows) — the admin-facing side of the availability model above.
