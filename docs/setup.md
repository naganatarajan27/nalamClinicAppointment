# Setup

See the root [README.md](../README.md) for day-to-day local setup (venv, `pip install`,
migrations, admin bootstrap, running both dev servers and both test suites). This file covers
*what* changes for a production deployment; see [deployment.md](deployment.md) for *where* to
actually host it (Render/Vercel, or a VPS) and the concrete step-by-step for each.

## Production configuration

`backend/app/main.py` refuses to start with `APP_ENV=production` if any of the following are
still at their insecure development defaults:

- `SESSION_SECRET` must be changed from the placeholder.
- `ADMIN_SESSION_COOKIE_SECURE` must be `true` (cookies are only sent over HTTPS).
- `DATABASE_URL` must not contain the example `user:password` credentials.

Also required for production, not currently enforced at startup:

- Serve over HTTPS end-to-end (the app does not terminate TLS itself).
- Set `FRONTEND_ORIGIN` to the real deployed frontend origin — CORS only allows that one origin,
  with credentials.
- Configure a real WhatsApp provider (`WHATSAPP_PROVIDER=cloud_api`) — see the README's WhatsApp
  section — and point Meta's webhook at `/api/v1/webhooks/whatsapp` with a strong
  `WHATSAPP_WEBHOOK_VERIFY_TOKEN`.
- Run `alembic upgrade head` as part of the deploy, before starting new app instances.
- Create the first admin with `python scripts/create_admin.py` from a trusted shell — there is
  no admin self-registration endpoint.

## Known scaling limitations

- `app/core/rate_limit.py` is an in-memory limiter; it resets per process and isn't shared
  across multiple backend instances. Replace with a shared store (e.g. Redis) before running more
  than one instance behind a load balancer.
- WhatsApp sends happen synchronously inside the request/response cycle. Under heavy load, move
  `NotificationService` calls to a background worker/queue instead.
