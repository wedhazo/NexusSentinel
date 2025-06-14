# Deploying NexusSentinel to Render

This document walks you through deploying the **NexusSentinel** platform—FastAPI backend, React frontend, and PostgreSQL database—to [Render](https://render.com).

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Render account** | Sign up at render.com (free tier is sufficient for a test run). |
| **Git repository** | Your NexusSentinel source must be on GitHub, GitLab, or Bitbucket and include the root `Dockerfile`, `web/Dockerfile`, and `render.yaml` created earlier. |
| **Docker knowledge (basic)** | Render builds from Dockerfiles automatically; no local Docker install is required for deployment. |
| **PostgreSQL migrations ready** | Alembic migrations should be in place. They will run automatically when `APPLY_MIGRATIONS=true`. |

---

## 2. Step-by-Step Deployment

### 2.1 Fork & Push (if necessary)

1. Fork or push the **NexusSentinel** repo to your own VCS account.  
2. Confirm that these files exist in the root branch you''ll deploy from:  
   - `Dockerfile` – backend API image  
   - `web/Dockerfile` – frontend image  
   - `render.yaml` – Render service definitions  
   - `.env.sample` or environment docs (do **not** commit real secrets).

### 2.2 Create the PostgreSQL database

1. In Render, click **New ? Database**.  
2. Choose **PostgreSQL** and name it `nexussentinel-db` (matching `render.yaml`).  
3. Select a plan (Starter works).  
4. Wait until Render finishes provisioning; keep the **connection string tab** open—you''ll need it for local testing.

`render.yaml` automatically binds API env vars (`DB_HOST`, `DB_USER`, …) to this database, so no manual copy-paste is required.

### 2.3 Deploy the Backend API

1. Click **New ? Web Service**.  
2. Select your NexusSentinel repo & branch.  
3. When prompted, choose **Docker** and ensure:
   - **Dockerfile path**: `Dockerfile`
   - **Docker context**: `.`  
4. Render detects `render.yaml` and offers to "Autogenerate Resources".  
   - Accept; it will create:
     - `nexussentinel-api` (backend)
     - `nexussentinel-web` (frontend)
     - if not created earlier, `nexussentinel-db` (database)  
5. Review the generated service. Key defaults:
   - **Port**: `8000`
   - **Health Check Path**: `/health`
   - Plan: change if you need more CPU/RAM.  
6. Click **Create Web Service**. The first build can take a few minutes.

### 2.4 Deploy the Frontend Web

Render will automatically queue the **nexussentinel-web** service defined in `render.yaml`.

If you skipped auto-generation:

1. Click **New ? Web Service** again.  
2. Set **Dockerfile path**: `web/Dockerfile`  
3. **Context**: `web`  
4. Port: `80`, Health Check: `/`  
5. Add environment variables (see next section).

### 2.5 Verify Everything

1. Open the backend URL shown by Render, e.g.  
   `https://nexussentinel-api.onrender.com/health` – should return `{"status":"healthy", ...}`  
2. Open the frontend URL, e.g.  
   `https://nexussentinel-web.onrender.com` – UI should load and retrieve data from the API.  
3. Swagger docs are at `/docs` on the API domain.

---

## 3. Environment Variable Configuration

`render.yaml` injects most variables automatically. Below is the meaning of each and whether you should override it.

| Variable | Service | Default / Source | Notes |
|----------|---------|------------------|-------|
| `DATABASE_URL` | API | Render DB connection string | Do **not** edit. |
| `APPLY_MIGRATIONS` | API | `true` | Set `false` to disable Alembic at boot. |
| `SECRET_KEY` | API | Auto-generated | You may rotate it by editing the value in the dashboard. |
| `CORS_ORIGINS` | API | `${RENDER_EXTERNAL_URL},https://nexussentinel-web.onrender.com` | Add extra domains separated by commas. |
| `VITE_API_BASE_URL` | Web | `https://nexussentinel-api.onrender.com/api/v1` | Update if you change the API service name/domain. |
| `NODE_ENV` | Web | `production` | Standard React build flag. |

Add any custom keys (e.g., third-party API tokens) via **Environment ? Add Env Var** in the Render dashboard or extend `render.yaml`.

---

## 4. Troubleshooting Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **Build fails with status 128** | Render couldn''t clone your repo (auth or submodules). | Check VCS permissions and any private submodules. |
| **Health check failed** | Backend didn''t start or port mismatch. | Confirm the `PORT` env on API is `8000` and health path is `/health`. Inspect logs. |
| **Database connection error** | DB not ready, wrong creds, or firewall. | Ensure the `nexussentinel-db` service exists and env mappings are intact. |
| **CORS errors in browser** | `CORS_ORIGINS` missing frontend domain. | Add full frontend URL to `CORS_ORIGINS` env var. |
| **Frontend shows blank page** | Wrong `VITE_API_BASE_URL` or build error. | Check browser console, verify env var, and redeploy web service. |
| **Migrations stuck** | Long-running Alembic script at startup. | View API logs; if necessary set `APPLY_MIGRATIONS=false` and run migrations manually via a job. |

### Quick Debug Commands

In the Render **Logs** tab of any service you can:

* Tail logs live.  
* Trigger manual redeploys.  
* Open a shell (`Console`) for container inspection (paid plans).

---

## 5. Updating / Redeploying

1. Commit and push code changes.  
2. Render auto-builds & deploys all affected services (based on paths).  
3. Monitor build logs; deployments atomically replace the previous version if the health check passes.

---

## 6. Cleaning Up

Delete services from the Render dashboard to stop billing. Remove the database last to avoid orphaned connections.

---

**Enjoy your fully-containerized NexusSentinel instance on Render!**  
For additional help, see the official [Render Docs](https://render.com/docs) or open an issue in the NexusSentinel repository.
