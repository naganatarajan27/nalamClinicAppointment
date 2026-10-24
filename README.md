# Nalam Clinic Appointment Booking

Patients request an appointment on a public booking page; a clinic administrator reviews each
request, accepts the requested slot or proposes a different one, and the patient gets a WhatsApp
message once their appointment is confirmed.

Full requirements/spec: [CLAUDE_REQUIREMENTS_NALAM_CLINIC.md](CLAUDE_REQUIREMENTS_NALAM_CLINIC.md).

## Stack

- **Frontend:** React + TypeScript + Vite (`frontend/`)
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic (`backend/`)
- **Database:** PostgreSQL (SQLite is used automatically in the backend test suite)
- **WhatsApp:** WhatsApp Business Cloud API, with a mock adapter for local development

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or Docker, via the included `docker-compose.yml`)

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Start a local Postgres database (or point `DATABASE_URL` at your own instance):

```bash
docker compose up -d db
```

Copy the environment template and adjust as needed:

```bash
cp ../.env.example ../.env   # repo-root .env is loaded by the backend via DATABASE_URL etc.
```

Run migrations:

```bash
alembic upgrade head
```

Create the first clinic administrator (there is no public admin self-registration route):

```bash
python scripts/create_admin.py --email admin@example.com
```

Run the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger / OpenAPI docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Backend tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Tests run against an isolated in-memory SQLite database (via `tests/conftest.py`) and the mock
WhatsApp adapter, so they need no running Postgres or WhatsApp credentials.

Run a single test:

```bash
pytest tests/test_admin_appointments.py::test_accept_confirms_appointment_and_sends_mock_notification
```

### Creating a new migration

```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on localhost:8000
npm run dev
```

The dev server runs on http://localhost:5173, matching the backend's default
`FRONTEND_ORIGIN` CORS allowlist entry.

- Booking page: `/`
- Admin login: `/admin/login`
- Admin dashboard: `/admin/appointments`

### Frontend tests

```bash
cd frontend
npm test
```

### Frontend build / lint

```bash
npm run build
npm run lint
```

## WhatsApp configuration

By default `WHATSAPP_PROVIDER=mock`, so no real WhatsApp messages are sent — every send is
logged with a line starting `MOCK WhatsApp ... NOT actually sent`, and the UI's notification
status still reflects the mock send/failure for development purposes.

To send real messages:

1. Set up a Meta WhatsApp Business Cloud API app and a verified phone number.
2. Get approval for two message templates (confirmation, alternate-slot proposal) — see the
   suggested wording in [CLAUDE_REQUIREMENTS_NALAM_CLINIC.md](CLAUDE_REQUIREMENTS_NALAM_CLINIC.md#7-whatsapp-notifications).
3. Set in `.env`:
   - `WHATSAPP_PROVIDER=cloud_api`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_BUSINESS_ACCOUNT_ID`
   - `WHATSAPP_API_VERSION` (e.g. `v20.0`)
   - `WHATSAPP_TEMPLATE_CONFIRMATION` / `WHATSAPP_TEMPLATE_ALTERNATE_SLOT` (your approved template names)
   - `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (a secret you choose, used to verify the webhook handshake)
4. Point your WhatsApp app's webhook at `POST /api/v1/webhooks/whatsapp` on your deployed backend,
   using the same verify token, to receive delivery-status updates.

The backend never claims a message was sent unless the provider's API call succeeded — see
`app/integrations/whatsapp/` for the adapter interface, mock adapter, and Cloud API adapter.

## Environment variables

See [.env.example](.env.example) (backend) and [frontend/.env.example](frontend/.env.example).
Never commit a real `.env` file or real secrets.

## Known limitations (first release)

- Doctor availability is a fixed 09:00–17:00, 30-minute-slot default (`app/services/availability_service.py`),
  not yet clinic-configurable.
- Login rate limiting is in-memory and per-process; a multi-instance production deployment should
  replace `app/core/rate_limit.py` with a shared store.
- WhatsApp notifications are sent synchronously within the request; a high-volume deployment may
  want to move this to a background task queue.
- Admin doctor management (`/api/v1/admin/doctors`) is minimal (list/create/update); there is no
  dedicated UI for it yet, so add doctors via the API or `/docs` Swagger UI.
