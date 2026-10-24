# Claude Code Requirements --- Nalam Clinic Appointment Booking

## 1. Project Overview

Build a simple, responsive web application called **Nalam Clinic
Appointment Booking**. Patients use the public website to request an
appointment. Clinic administrators sign in to review requests, confirm a
requested slot, or propose a different date/time. Once the patient's
appointment is confirmed, the system sends a WhatsApp confirmation
message.

This document is the source of truth for implementation. Before coding,
inspect the existing repository and preserve its conventions where
practical. If the repository is empty, create the project structure
described below.

## 2. Technology Stack

-   **Frontend:** React with TypeScript, using Vite.
-   **Backend:** Python 3.11+ with FastAPI.
-   **API style:** REST/JSON, versioned under `/api/v1`.
-   **Database:** PostgreSQL for persistent appointment and admin data;
    use SQLAlchemy 2.x and Alembic migrations.
-   **Validation:** Pydantic models on the API; client-side validation
    for usability.
-   **Configuration:** Environment variables loaded from `.env` locally.
    Never commit secrets.
-   **WhatsApp:** Use the official WhatsApp Business Platform / Cloud
    API through a backend integration service. Keep credentials
    server-side. Do not use unofficial WhatsApp automation.
-   **Testing:** Pytest for backend; Vitest and React Testing Library
    for frontend.
-   **API documentation:** FastAPI OpenAPI/Swagger documentation.

If the repository already uses an equivalent tool for a listed concern,
inspect it first and explain any proposed change before replacing it.

## 3. User Roles

### 3.1 Patient (public user)

-   Can submit an appointment request without creating an account.
-   Can see a clear success message after the request is saved.
-   Must not be able to access the admin dashboard or other patients'
    information.

### 3.2 Clinic administrator

-   Must sign in before accessing any admin functionality.
-   Can view and filter appointment requests.
-   Can accept a requested date/time or propose a new date/time.
-   Can add an optional internal note.
-   Can see whether a WhatsApp message was sent successfully or failed.
-   Can log out securely.

## 4. Patient Booking Page

Create a clean, minimal, mobile-friendly React page branded **Nalam
Clinic**. Avoid unnecessary animations, clutter, or multi-step flows.
Use accessible labels, clear validation messages, and a visible loading
state during submission.

### Required form fields

1.  **Patient name** --- required text field.
2.  **Patient type** --- required selection:
    -   New patient
    -   Existing patient
3.  **Phone number** --- required; validate a reasonable international
    phone format and show country-code guidance. Do not assume that the
    phone number and WhatsApp number are the same.
4.  **WhatsApp number** --- required if WhatsApp confirmations are part
    of the workflow; validate and normalize to international format
    (E.164 where possible).
5.  **Preferred doctor** --- required selection populated from active
    doctors configured by the clinic. If doctor management is not in
    scope for the first release, support a configurable list from the
    backend rather than hard-coding it only in the UI.
6.  **Preferred appointment date** --- required; do not allow dates in
    the past.
7.  **Preferred appointment time** --- required; show
    available/configured slots where feasible. Prevent selecting a slot
    that is known to be unavailable. Treat this as a *request*, not a
    confirmed booking, until an administrator accepts it.
8.  **Symptoms / reason for visit** --- required, short multiline field;
    set a reasonable maximum length (for example, 1,000 characters).
    Tell patients not to enter emergency details or unnecessary
    sensitive information.

### Booking-page behavior

-   Show the clinic name and a short explanation: "Submit your preferred
    appointment time. The clinic will confirm it or suggest another
    time."
-   On submit, validate the fields and display field-level errors.
-   Prevent duplicate submissions while a request is in progress.
-   On success, show a reference number and a message that the request
    is pending clinic review.
-   Do not tell the patient that an appointment is confirmed until the
    admin accepts a slot.
-   Handle API errors gracefully without exposing stack traces or
    internal details.
-   Include a short notice that this form is for appointment requests
    and is not an emergency service.
-   Use a configurable clinic timezone; default to `Asia/Kolkata` unless
    the clinic specifies otherwise.

## 5. Administrator Login and Dashboard

Create a separate route such as `/admin/login` and a protected dashboard
at `/admin/appointments`.

### Login

-   Email/username and password.
-   Secure password hashing (Argon2id or bcrypt).
-   Use secure session cookies or a well-implemented token strategy.
    Prefer HttpOnly, Secure (in production), SameSite cookies for
    browser sessions.
-   Apply login rate limiting and generic error messages.
-   Do not provide a public admin self-registration route.
-   Provide a documented, safe way to create the first admin (CLI
    command or seed script); never hard-code production credentials.

### Dashboard

Show appointment requests in a simple table or responsive list.
Include: - Reference number - Patient name - Patient type - Phone
number - WhatsApp number (mask in list view where practical) - Preferred
doctor - Requested date/time - Symptoms/reason (show only to authorized
admin users) - Status - Created date/time - WhatsApp notification status

Allow the admin to: - Search by reference number or patient name. -
Filter by status and date. - Open an appointment detail view. - **Accept
requested slot:** confirm the requested doctor/date/time, update status
to `CONFIRMED`, and trigger a WhatsApp confirmation. - **Suggest a new
slot:** enter a proposed date/time and, if needed, a different doctor.
Update status to `ALTERNATE_PROPOSED` and send a WhatsApp message asking
the patient to contact the clinic or confirm the proposed slot through a
clearly defined workflow. - Add an internal note that is not visible to
patients. - View notification delivery status and retry a failed
notification safely. - Log out.

### Alternate-slot workflow

For the first version, do not imply that a suggested slot is confirmed.
Store it as a proposal. Send the patient a WhatsApp message with the
proposed slot and instructions for confirming it (for example, call the
clinic or use a patient-facing confirmation link if that feature is
implemented). If a confirmation link is implemented, use a random,
single-use, expiring token and do not expose sequential appointment IDs.
The final appointment status must become `CONFIRMED` only after the
patient accepts the proposed slot or the admin explicitly confirms it
according to the clinic's chosen process.

## 6. Appointment Statuses

Use explicit, documented status values: - `PENDING` --- request
submitted; awaiting admin review. - `CONFIRMED` --- a specific
appointment slot has been confirmed. - `ALTERNATE_PROPOSED` --- clinic
has suggested a different slot; patient response is pending. -
`CANCELLED` --- cancelled by an authorized admin or through a future
patient cancellation flow. - `COMPLETED` --- visit completed, if the
clinic chooses to track this.

Keep status transitions validated on the backend. Record who performed
each admin action and when.

## 7. WhatsApp Notifications

### Confirmation message

After the admin accepts the appointment, send a WhatsApp message to the
patient's WhatsApp number. Use an approved WhatsApp Business message
template where required by Meta's rules and the conversation window.

Suggested message content (final wording/template must be approved and
configured with the WhatsApp provider):

> Hello {{patient_name}}, your appointment at Nalam Clinic is confirmed.
> Doctor: {{doctor_name}} Date: {{appointment_date}} Time:
> {{appointment_time}} Reference: {{reference_number}} Please contact
> the clinic if you need to make a change.

### Alternate-slot message

> Hello {{patient_name}}, Nalam Clinic cannot confirm your originally
> requested time. We would like to suggest {{proposed_date}} at
> {{proposed_time}} with {{doctor_name}}. Please {{next_step}} to
> confirm or contact the clinic. Reference: {{reference_number}}.

### Integration requirements

-   Implement a `WhatsAppNotificationService` abstraction so provider
    calls can be mocked in tests.
-   Use the official WhatsApp Business Platform / Cloud API or a
    documented approved provider.
-   Keep access tokens, phone-number IDs, and other secrets in backend
    environment variables.
-   Never send messages directly from React.
-   Persist each notification attempt with status, timestamp, provider
    message ID (when available), and a sanitized error summary.
-   Make retries idempotent where possible to avoid duplicate messages.
-   Do not mark the appointment notification as sent until the provider
    accepts the message. Distinguish `QUEUED`, `SENT/ACCEPTED`,
    `DELIVERED` (only if delivery webhook confirms it), and `FAILED` as
    supported by the provider.
-   Add webhook handling for delivery status if configured; verify
    webhook requests according to the provider's documented mechanism.
-   If WhatsApp credentials are missing in local development, use a mock
    adapter and clearly log that it is a mock. Never claim that a real
    message was sent.
-   Provide setup documentation for creating/configuring the WhatsApp
    Business API integration, templates, webhook, and environment
    variables.

## 8. REST API Requirements

Prefix all endpoints with `/api/v1`.

### Public endpoints

-   `GET /doctors` --- return active doctors suitable for booking.
-   `GET /availability?doctor_id=...&date=YYYY-MM-DD` --- return
    configured available slots if slot management is implemented.
-   `POST /appointments` --- validate and create a `PENDING` appointment
    request; return the public reference number and status.
-   Optional: `GET /appointments/{public_reference}` --- only if
    designed to expose minimal information safely and protected against
    enumeration. Never return symptoms or contact details from an
    unauthenticated lookup.

### Admin endpoints

-   `POST /admin/auth/login` --- authenticate admin.
-   `POST /admin/auth/logout` --- end session.
-   `GET /admin/auth/me` --- current admin identity.
-   `GET /admin/appointments` --- paginated list with filters.
-   `GET /admin/appointments/{id}` --- appointment details for
    authorized admins.
-   `PATCH /admin/appointments/{id}/accept` --- accept the requested
    slot and confirm appointment.
-   `PATCH /admin/appointments/{id}/propose-slot` --- save an alternate
    slot and trigger its notification.
-   `PATCH /admin/appointments/{id}/status` --- only for documented,
    allowed transitions such as cancellation/completion.
-   `POST /admin/appointments/{id}/notifications/retry` --- safely retry
    a failed notification.
-   `GET /admin/doctors` and admin doctor-management endpoints if doctor
    maintenance is included in this release.

### API conventions

-   Use Pydantic request and response schemas; never return ORM objects
    directly.
-   Use appropriate HTTP status codes and a consistent error response
    format.
-   Validate dates, times, doctor IDs, field lengths, and status
    transitions server-side.
-   Add pagination to dashboard list endpoints.
-   Generate a random, non-sequential public reference (for example,
    `NAL-` plus a random suffix).
-   Use database transactions for appointment state changes and
    notification-job creation.
-   Add idempotency protection or equivalent safeguards for repeated
    form submissions and admin actions where appropriate.
-   Add CORS configuration using an explicit allowlist from environment
    configuration; do not allow all origins in production.

## 9. Suggested Data Model

### `admins`

-   `id` (UUID primary key)
-   `email` (unique)
-   `password_hash`
-   `is_active`
-   `created_at`, `updated_at`
-   `last_login_at`

### `doctors`

-   `id` (UUID primary key)
-   `display_name`
-   `specialty` (optional)
-   `is_active`
-   `created_at`, `updated_at`

### `appointments`

-   `id` (UUID primary key)
-   `public_reference` (unique, random)
-   `patient_name`
-   `patient_type` (`NEW` or `EXISTING`)
-   `phone_number`
-   `whatsapp_number`
-   `doctor_id` (foreign key)
-   `requested_date`
-   `requested_time`
-   `confirmed_doctor_id` (nullable foreign key if different doctor is
    allowed)
-   `confirmed_date` (nullable)
-   `confirmed_time` (nullable)
-   `proposed_date` (nullable)
-   `proposed_time` (nullable)
-   `proposed_doctor_id` (nullable foreign key)
-   `symptoms`
-   `status`
-   `admin_note` (nullable; never returned by public endpoints)
-   `created_at`, `updated_at`
-   `reviewed_by_admin_id` (nullable foreign key)
-   `reviewed_at` (nullable)

### `notification_attempts`

-   `id` (UUID primary key)
-   `appointment_id` (foreign key)
-   `channel` (initially `WHATSAPP`)
-   `notification_type` (`CONFIRMATION` or `ALTERNATE_PROPOSAL`)
-   `status`
-   `provider_message_id` (nullable)
-   `attempt_count`
-   `last_error_summary` (sanitized, nullable)
-   `created_at`, `updated_at`, `sent_at` (nullable)

Add indexes for appointment status, requested date, doctor, creation
time, and public reference. Use migrations for schema changes.

## 10. Security, Privacy, and Reliability

-   Treat symptoms/reason for visit and contact details as sensitive
    personal data.
-   Collect only data needed to arrange the appointment.
-   Show a concise privacy notice and obtain any consent required for
    storing contact details and sending appointment updates via
    WhatsApp.
-   Restrict patient data and symptoms to authenticated, authorized
    clinic administrators.
-   Use HTTPS in production.
-   Protect admin actions against CSRF if cookie-based authentication is
    used; use appropriate SameSite cookies and CSRF tokens where needed.
-   Apply input validation, output encoding, secure headers, rate
    limiting, and login throttling.
-   Avoid logging patient symptoms, full phone numbers, credentials,
    access tokens, or other sensitive content.
-   Do not include personal data in URLs, analytics events, or error
    messages.
-   Configure retention/deletion policies with the clinic; do not retain
    patient information indefinitely by default.
-   Make secrets configurable through environment variables and provide
    a `.env.example` containing placeholders only.
-   Use structured application logs with request IDs, without sensitive
    patient data.
-   Handle database and WhatsApp provider outages gracefully.
-   Add authorization checks to every admin endpoint, not just the React
    route.
-   Use database constraints and transactions to avoid inconsistent
    status updates.
-   Do not present the application as an emergency medical service.

## 11. UI and Accessibility

-   Use a simple, professional clinic look: white background, calm
    blue/teal accents, readable typography, and clear spacing.
-   Responsive on mobile, tablet, and desktop.
-   Use semantic HTML, associated labels, keyboard-accessible controls,
    visible focus states, and accessible error announcements.
-   Show loading, success, empty, and error states.
-   Confirm potentially destructive admin actions such as cancellation.
-   Format dates/times consistently using the configured clinic
    timezone.
-   Keep the public booking page and admin dashboard visually distinct
    but consistent in branding.

## 12. Repository Structure

Create a maintainable structure similar to:

``` text
nalam-clinic/
  frontend/
    src/
      api/
      components/
      features/
        booking/
        admin-auth/
        admin-appointments/
      pages/
      types/
      utils/
    public/
    tests/
    package.json
    vite.config.ts
  backend/
    app/
      api/v1/
      core/
      db/
      models/
      schemas/
      repositories/
      services/
      integrations/
        whatsapp/
      main.py
    alembic/
    tests/
    pyproject.toml
  docs/
    architecture.md
    setup.md
    api.md
  .env.example
  .gitignore
  README.md
```

Adjust the structure if the repository has established conventions, but
preserve clear separation between UI, API routes, business logic,
persistence, and external integrations.

## 13. Environment Variables

Document the following in `.env.example` using placeholder values only:

``` dotenv
APP_ENV=development
APP_NAME=Nalam Clinic
CLINIC_TIMEZONE=Asia/Kolkata
FRONTEND_ORIGIN=http://localhost:5173
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/nalam_clinic
SESSION_SECRET=replace-with-a-long-random-secret
ADMIN_SESSION_COOKIE_SECURE=false

WHATSAPP_PROVIDER=mock
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_API_VERSION=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
WHATSAPP_TEMPLATE_CONFIRMATION=
WHATSAPP_TEMPLATE_ALTERNATE_SLOT=
```

Validate required production configuration at startup. Never commit a
real secret. Document that the real WhatsApp integration requires
provider setup and approved templates.

## 14. Testing and Acceptance Criteria

Claude must implement tests and verify the following:

### Patient booking

-   A valid form creates a `PENDING` request and returns a public
    reference.
-   Required-field and invalid phone/date/time inputs are rejected.
-   Past dates cannot be submitted.
-   The UI displays a pending-review message, not a false confirmation.
-   Public responses do not expose internal IDs, admin notes, symptoms
    through lookup, or other patients' details.

### Admin access and review

-   Unauthenticated requests cannot access admin APIs.
-   Invalid credentials do not reveal whether an account exists.
-   Authorized admins can view and filter appointments.
-   Accepting a request updates the status and confirmed slot correctly.
-   Suggesting an alternate slot stores the proposal and does not
    falsely mark the appointment confirmed.
-   Invalid status transitions are rejected.
-   A non-admin cannot perform admin actions.

### WhatsApp

-   Accepting a slot triggers the confirmation notification workflow.
-   Proposing a slot triggers the alternate-slot workflow.
-   Provider failures are recorded and do not corrupt appointment state.
-   Retry behavior avoids accidental duplicate sends where possible.
-   Mock mode is clearly identified and is used in tests.
-   The UI distinguishes notification accepted/sent, delivered (if
    supported), and failed.

### Engineering quality

-   Database migrations run successfully.
-   Backend and frontend tests pass.
-   API docs are available in development.
-   No secrets are committed.
-   README documents setup, migrations, admin bootstrap, running tests,
    and WhatsApp configuration.
-   Include sample development data only if it is clearly marked as
    non-production.
-   Provide a concise implementation summary, commands executed, test
    results, and known limitations.

## 15. Implementation Plan for Claude Code

Follow this sequence:

1.  Inspect the repository and summarize its current state.
2.  Identify ambiguities and state assumptions. Ask only questions that
    block implementation; otherwise use the defaults in this document.
3.  Propose a short implementation plan and directory structure before
    making substantial changes.
4.  Implement database models and migrations, backend
    schemas/services/API routes, and tests.
5.  Implement the React booking page and admin login/dashboard,
    including loading and error states.
6.  Implement the WhatsApp service interface, mock adapter, and real
    provider adapter with configuration.
7.  Run migrations, lint/type checks where configured, and tests. Fix
    failures rather than merely reporting them.
8.  Update setup/API/architecture documentation and `.env.example`.
9.  Review security, privacy, authorization, validation, status
    transitions, and notification failure handling.
10. Finish with a summary of files created/changed, how to run the app,
    test results, environment setup, and remaining production setup
    steps.

Do not claim a real WhatsApp message was sent unless the real provider
confirms the relevant result. Do not leave core booking or admin
workflows as TODOs or placeholder screens. If provider credentials are
unavailable, complete and test the mock integration and clearly document
what must be configured for live messaging.
