# NexusSentinel – Docker & Deployment Guide

A one-page reference for building, running and shipping the NexusSentinel FastAPI + PostgreSQL stack with Docker & Docker Compose.

---

## 1. Prerequisites

| Tool | Minimum version | Check |
|------|-----------------|-------|
| Docker Engine | 20.10+ | `docker --version` |
| Docker Compose | v2 plugin (`docker compose`) | `docker compose version` |
| Git (optional) | 2.30+ | `git --version` |

> Windows users: ensure WSL 2 is enabled for best performance.

---

## 2. Project Layout Recap

```
NexusSentinel/
├─ app/                   # FastAPI code (app instance in app/main.py)
├─ Dockerfile             # Multi-stage build
├─ entrypoint.sh          # Wait-for-DB + optional Alembic
├─ docker-compose.yml     # API + PostgreSQL (+ pgAdmin)
├─ .env                   # Secrets & runtime config
└─ ...
```

The **.env** file is shared by both containers. Populate at least:

```env
DB_USER=postgres
DB_PASSWORD=supersecret
DB_NAME=nexussentinel
SECRET_KEY=replace_me_with_secure_value
```

---

## 3. Building & Running

### 3.1 Local development (with live-reload mounts)

```bash
# inside project root
docker compose --profile dev up --build
```

* API accessible: <http://localhost:8000>
* Swagger docs: <http://localhost:8000/docs>
* PostgreSQL: `localhost:5432`
* pgAdmin (dev profile): <http://localhost:5050>

### 3.2 Production-style run

```bash
docker compose up --build -d        # detached
docker compose logs -f api          # tail API logs
```

> In prod you might **remove** the `volumes:` bind mount for `./app` to ship an immutable image.

---

## 4. Useful Commands

| Task | Command |
|------|---------|
| **Re-build image** | `docker compose build api` |
| **Stop services** | `docker compose down` |
| Stop & **wipe volumes** | `docker compose down -v` |
| **View logs** (all) | `docker compose logs -f` |
| Exec into API | `docker compose exec api bash` |
| Exec into DB | `docker compose exec db psql -U $DB_USER $DB_NAME` |
| **Apply Alembic migrations** | `docker compose exec api alembic upgrade head` |
| **Run PyTest** inside container | `docker compose exec api pytest -q` |

---

## 5. Pushing to a Registry

```bash
# 1. Tag
docker tag nexussentinel-api:latest ghcr.io/your-user/nexussentinel:1.0.0

# 2. Login & push
docker login ghcr.io
docker push ghcr.io/your-user/nexussentinel:1.0.0
```

Update `docker-compose.yml` on server to `image: ghcr.io/your-user/nexussentinel:1.0.0` instead of build context.

---

## 6. Deployment on a Remote Host (example)

```bash
# Copy compose file & env
scp docker-compose.yml .env user@server:/opt/nexussentinel
ssh user@server
cd /opt/nexussentinel
docker compose pull           # if using remote image
docker compose up -d
```

Add a **systemd** unit or schedule with **Watchtower** for automatic updates.

---

## 7. Health Checks

* **API** → `/health` (200 = OK)  
  Compose health-check retries 3× before marking container unhealthy.
* **PostgreSQL** → `pg_isready` probe in compose file.

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `api` stuck `Waiting for PostgreSQL…` | verify DB creds in `.env`, ports not in use |
| `FATAL: password authentication failed` | passwords mismatch between `.env` and existing volume → delete volume or update creds |
| CORS blocked | edit `CORS_ORIGINS` in `.env` |
| pgAdmin refuses connection | ensure pgAdmin profile enabled, DB host `db`, port `5432` |

---

## 9. Clean-up Everything

```bash
docker compose down -v --remove-orphans
docker image prune -f
docker volume prune -f
```

This removes containers, anonymous volumes, and dangling images.

---

Happy shipping 🚀!
