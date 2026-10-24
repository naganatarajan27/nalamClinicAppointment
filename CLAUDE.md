# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Patients submit an appointment request on a public page; a clinic administrator reviews it,
accepts the requested slot or proposes a different one, and the patient gets a WhatsApp message
once confirmed. Full requirements/spec (source of truth for intended behavior, not just history):
[CLAUDE_REQUIREMENTS_NALAM_CLINIC.md](CLAUDE_REQUIREMENTS_NALAM_CLINIC.md). Setup/ops details:
[README.md](README.md); deeper design notes: [docs/architecture.md](docs/architecture.md),
[docs/api.md](docs/api.md), [docs/setup.md](docs/setup.md).

Never claim a real WhatsApp message was sent unless the real provider confirmed it. The mock
adapter (`WHATSAPP_PROVIDER=mock`, the default) is used in local dev and in all tests.

## Commands

### Backend (`backend/`)

```bash
cd backend && source .venv/bin/activate   # venv created with: python3 -m venv .venv && pip install -e ".[dev]"

uvicorn app.main:app --reload --port 8000   # run API (Swagger UI at /docs)
pytest                                       # run all tests (in-memory SQLite, mock WhatsApp)
pytest tests/test_admin_appointments.py::test_accept_confirms_appointment_and_sends_mock_notification  # single test

alembic upgrade head                         # apply migrations
alembic revision --autogenerate -m "..."     # new migration after changing app/models/

python scripts/create_admin.py --email admin@example.com   # bootstrap the first admin (no public signup route)
```

Local Postgres: `docker compose up -d db` (repo-root `docker-compose.yml`). Config is read from
`.env` via `app/core/config.py` (`pydantic-settings`); see `.env.example`.

### Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev      # Vite dev server on :5173 (matches backend FRONTEND_ORIGIN default)
npm run build    # tsc -b && vite build
npm run lint      # oxlint
npm test          # vitest run
npm run test:watch
```

`VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`) is read in `src/api/client.ts`.

## Architecture

### Backend layering (`backend/app/`)

Strictly one-directional: `api/v1/` (FastAPI routers; HTTP <-> Pydantic, maps domain exceptions
to status codes) → `services/` (business logic + transactions + the status state machine) →
`repositories/` (SQLAlchemy queries only) → `models/` (ORM + `enums.py`). Routes never touch the
ORM directly or return ORM objects — always through `schemas/`. See
[docs/architecture.md](docs/architecture.md) for the full breakdown, including the appointment
status state machine (`ALLOWED_STATUS_TRANSITIONS` in `app/models/enums.py`) and the
notification/webhook flow.

`app/integrations/whatsapp/` is an abstract `WhatsAppNotificationService` with two
implementations selected by `WHATSAPP_PROVIDER` via `factory.get_whatsapp_adapter()`:
`MockWhatsAppAdapter` (logs only) and `WhatsAppCloudApiAdapter` (real Meta Graph API calls). This
is what tests mock instead of hitting the network.

Auth is a signed cookie (`itsdangerous`, no sessions table) plus a double-submit CSRF cookie —
every mutating admin request needs `X-CSRF-Token` matching the `nalam_csrf_token` cookie
(`app/api/deps.py:require_csrf`). Login is rate-limited in-memory per `ip:email`
(`app/core/rate_limit.py` — documented as not safe for multi-instance deployments as-is).

### Frontend (`frontend/src/`)

`api/` — two fetch wrappers (`publicApi.ts`, `adminApi.ts`) on a shared `client.ts` that injects
the CSRF header on non-GET requests. `features/booking`, `features/admin-auth`,
`features/admin-appointments` are the three independent flows; `pages/` are thin route-level
compositions; `AuthContext` (`features/admin-auth/`) is what `RequireAuth` uses to gate
`/admin/appointments*`.

### Tests

Backend tests (`backend/tests/`) override the `get_db` FastAPI dependency with a fresh in-memory
SQLite engine per test (`conftest.py`) — no real Postgres needed. Frontend tests
(`frontend/tests/`) mock the `api/*` modules with `vitest`'s `vi.spyOn` rather than hitting a
real backend.

## Known limitations (see README for the full list)

Fixed (non-configurable) clinic hours for availability; in-memory login rate limiter; WhatsApp
sends happen synchronously in-request; admin doctor management has no dedicated UI yet (use
`/docs` Swagger UI or the API directly).
