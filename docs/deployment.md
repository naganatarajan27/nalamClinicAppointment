# Deployment

This app is two independently deployable pieces: a FastAPI backend (+ Postgres) and a static
React frontend. Either path below gets you a real `https://` URL. Pick **Option A** unless you
specifically want to run your own server.

Both options assume the code is pushed to a GitHub repository — push this repo there first if it
isn't already:

```bash
git remote add origin https://github.com/<you>/nalam-clinic.git
git push -u origin master
```

## Option A: Render (backend + Postgres) + Vercel (frontend) — recommended

Free to start, no server to manage, both give you HTTPS and a custom domain for free.

### 1. Database + backend on Render

1. Sign up at [render.com](https://render.com) and connect your GitHub account.
2. **New → PostgreSQL** — name it `nalam-clinic-db`, pick the free or starter plan. Once created,
   copy its **Internal Database URL**.
3. **New → Web Service** → pick this repo.
   - **Root directory:** `backend`
   - **Runtime:** Docker (Render detects `backend/Dockerfile` automatically)
   - **Instance type:** the free tier works for evaluation; use a paid instance for anything real
     (the free tier sleeps after inactivity, which delays the first request after idle).
4. Add environment variables (Render's dashboard → Environment):
   ```
   APP_ENV=production
   DATABASE_URL=<the Internal Database URL from step 2, with postgresql+psycopg:// instead of postgresql://>
   FRONTEND_ORIGIN=https://<your-vercel-app>.vercel.app   # update after step 2 below
   SESSION_SECRET=<generate: python3 -c "import secrets; print(secrets.token_urlsafe(48))">
   ADMIN_SESSION_COOKIE_SECURE=true
   WHATSAPP_PROVIDER=mock   # switch to cloud_api once you've done the WhatsApp setup in the README
   EMAIL_PROVIDER=mock      # switch to smtp once you've set SMTP_* vars (see README)
   ```
   `DATABASE_URL`'s scheme must be `postgresql+psycopg://` (SQLAlchemy's driver prefix) — Render
   gives you a plain `postgresql://` URL, so edit the scheme when pasting it in.
5. Deploy. Render builds the Docker image and runs the container's `CMD`, which applies
   migrations (`alembic upgrade head`) before starting `uvicorn`. Watch the deploy logs for the
   `Running upgrade ...` lines to confirm.
6. Note the service's public URL, e.g. `https://nalam-clinic-backend.onrender.com` — you'll need
   it for the frontend's `VITE_API_BASE_URL`.
7. Bootstrap the first admin: Render dashboard → your service → **Shell**, then:
   ```bash
   python scripts/create_admin.py --email admin@yourclinic.com
   ```

### 2. Frontend on Vercel

1. Sign up at [vercel.com](https://vercel.com), **Add New → Project**, import this repo.
2. **Root directory:** `frontend`. Vercel auto-detects the Vite framework preset (build command
   `npm run build`, output directory `dist`). `frontend/vercel.json` is already set up for SPA
   routing, so refreshing `/admin/appointments` won't 404.
3. Add an environment variable: `VITE_API_BASE_URL` = `https://<your-render-service>.onrender.com/api/v1`
   (the backend URL from step 1.6, with `/api/v1` appended).
4. Deploy. Note the resulting URL, e.g. `https://nalam-clinic.vercel.app`.
5. Go back to Render and update `FRONTEND_ORIGIN` to that exact URL, then redeploy the backend —
   CORS only allows the one configured origin, so this step is required for the booking form and
   admin dashboard to be able to call the API at all.

### 3. Custom domain (optional)

Both Render and Vercel let you attach a custom domain for free (Project/Service **Settings →
Domains**) — point your DNS at the value they give you, and they issue a free TLS certificate
automatically. If you do this for the frontend, update `FRONTEND_ORIGIN` on the backend to the
new domain too.

## Option B: a single VPS with Docker Compose

More control, roughly $5-10/month (DigitalOcean, Hetzner, Linode droplet — 1GB RAM is enough).
You manage OS updates and backups yourself.

1. Provision an Ubuntu VPS, point a domain's DNS `A` record at its IP, then SSH in and install
   Docker: https://docs.docker.com/engine/install/ubuntu/
2. Clone the repo onto the server and create a production `.env` at the repo root (copy
   `.env.example`, fill in real values — `SESSION_SECRET`, `ADMIN_SESSION_COOKIE_SECURE=true`,
   `FRONTEND_ORIGIN=https://yourdomain.com`, WhatsApp/email credentials per the README).
3. Build the frontend as static files and serve them (and proxy `/api` to the backend, and get
   TLS) with a reverse proxy. [Caddy](https://caddyserver.com/) is the simplest option — it
   issues and renews Let's Encrypt certificates automatically. Example `Caddyfile`:
   ```
   yourdomain.com {
       reverse_proxy /api/* backend:8000
       root * /srv/frontend-dist
       try_files {path} /index.html
       file_server
   }
   ```
4. Add a `frontend` build step and a `caddy` service to `docker-compose.yml` (not included by
   default, since the repo-root compose file is meant for local dev):
   ```yaml
   caddy:
     image: caddy:2-alpine
     restart: unless-stopped
     ports: ["80:80", "443:443"]
     volumes:
       - ./Caddyfile:/etc/caddy/Caddyfile
       - ./frontend/dist:/srv/frontend-dist:ro
       - caddy_data:/data
   ```
   Build the frontend once with `VITE_API_BASE_URL=https://yourdomain.com/api/v1 npm run build`
   (adjust the Caddyfile route or `VITE_API_BASE_URL` if you don't proxy `/api` through the same
   domain) before starting Caddy, and rebuild it on every frontend update.
5. `docker compose --env-file .env up -d --build` starts Postgres, the backend (migrations run
   automatically), and Caddy.
6. Bootstrap the admin: `docker compose exec backend python scripts/create_admin.py --email admin@yourclinic.com`.

## Common to both options

### WhatsApp and email

Both are in mock mode (logged, not sent) until configured. See the README's
[WhatsApp configuration](../README.md#whatsapp-configuration) and
[Email configuration](../README.md#email-configuration) sections — the only deployment-specific
part is that your WhatsApp webhook must point at your **public** backend URL:
`https://<your-backend-domain>/api/v1/webhooks/whatsapp`.

### Doctors and availability

The database starts empty. After deploying, sign in as the admin you bootstrapped and, from
**Doctors & availability** (`/admin/doctors`), add your clinic's doctors and their weekly
available hours — the public booking page has nothing to offer patients until this is done.

### Deploying updates

- **Render / Vercel:** push to the branch they're tracking; both auto-deploy and Render re-runs
  migrations on every deploy (it's in the container's start command).
- **VPS:** `git pull`, rebuild the frontend if it changed, then
  `docker compose up -d --build backend`.

### Going-live checklist

- [ ] `ADMIN_SESSION_COOKIE_SECURE=true` and the site is served over HTTPS (required for the
      session cookie to be sent at all once that flag is on).
- [ ] `SESSION_SECRET` is a real random value, not the placeholder.
- [ ] `FRONTEND_ORIGIN` on the backend exactly matches the frontend's real URL (scheme + host,
      no trailing slash).
- [ ] At least one doctor with configured availability exists.
- [ ] First admin created via `scripts/create_admin.py`; no admin self-registration route exists.
- [ ] A real booking → accept → notification round-trip has been tested against the deployed
      backend (mock mode is fine for this — it confirms wiring, not real delivery).
- [ ] WhatsApp/email switched from `mock` to real providers only once you're ready for patients
      to actually receive messages — mock mode never sends anything, by design.
