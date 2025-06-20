# NexusSentinel – ML Services Deployment Guide  
Location: `ml_services/deployment/README.md`

This guide explains how to spin-up **all auxiliary machine–learning services** that extend the main NexusSentinel API with advanced sentiment, forecasting and real-time signalling features.

---

## 1 .  Prerequisites

| Requirement | Purpose | Quick Check |
|-------------|---------|-------------|
| **Docker 20.10+** | Container engine | `docker --version` |
| **Docker Compose v2** | Multi-service orchestration | `docker compose version` |
| **4 GB RAM (min)** | FinBERT + LightGBM | – |
| **NVIDIA GPU + Driver** (optional) | LLaMA-3 8 B quantized | `nvidia-smi` |
| **NVIDIA Container Toolkit** | GPU passthrough to containers | see <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/> |

> ⚠️ You can run the stack **without a GPU** – the LLaMA service will simply fail to start or can be commented out in `docker-compose.yml`.

---

## 2 .  Folder Structure

```
ml_services/
├── sentiment_service/           # FinBERT API  (port 8000)
├── llama3_sentiment_service/    # LLaMA-3 8B    (port 8001, GPU)
├── signal_generator/            # LightGBM      (port 8002)
├── price_forecast_service/      # TFT           (port 8003)
├── websocket_signal_server/     # WebSocket hub (port 8004)
├── infra_redis_zmq/             # Redis + ZeroMQ publisher/subscriber
└── deployment/
    ├── docker-compose.yml
    └── README.md  ← you are here
```

All services are **self-contained micro-services** – you may deploy only the ones you need.

---

## 3 .  Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Hostname injected into `sentiment_service` |
| `MODEL_PATH` | service-specific | Path to checkpoint (`tft_best.ckpt`, `lgbm_model.pkl` …) |
| `NVIDIA_VISIBLE_DEVICES` | `all` | Override in compose to limit GPU usage |
| `FINBERT_CACHE_TTL` | `3600` | Seconds FinBERT predictions stay in Redis |

Create a `.env` file in this directory to override any value.  
Compose automatically loads it.

---

## 4 .  Quick Start

```bash
# Run everything (first build can take a few minutes)
cd ml_services/deployment
docker compose up --build

# Tail logs of a single service
docker compose logs -f sentiment_service
```

Healthy startup looks like:

```
sentiment_service_1  | Uvicorn running on :8000
llama3_sentiment_service_1 | Loaded LLaMA-3 on CUDA
signal_generator_1   | Model loaded: LightGBM
price_forecast_service_1 | Model type: Dummy (rule-based)
websocket_signal_server_1 | Starting WebSocket Signal Server
```

Stop & remove:

```bash
docker compose down -v
```

---

## 5 .  Service Matrix

| Service | Port | Model | Depends On | GPU |
|---------|------|-------|-----------|-----|
| `sentiment_service` | 8000 | FinBERT | Redis | ❌ |
| `llama3_sentiment_service` | 8001 | LLaMA-3 8 B (8-bit) | Redis | ✅ (optional) |
| `signal_generator` | 8002 | LightGBM / dummy | sentiment_service | ❌ |
| `price_forecast_service` | 8003 | Temporal Fusion Transformer / dummy | — | ❌ / ✅ |
| `websocket_signal_server` | 8004 | – | sentiment_service, signal_generator | ❌ |
| `redis` | 6379 | in-memory cache | — | ❌ |
| `zmq_publisher` | 5556 | ZeroMQ PUB | – | ❌ |
| `zmq_subscriber` | – | ZeroMQ SUB | `zmq_publisher` | ❌ |

> All containers share the network `nexussentinel-ml-network`.

---

## 6 .  Integrating with the Main API

The monolithic FastAPI backend (folder `app/`) already exposes proxy endpoints:

| Upstream Service | Gateway Route | Method |
|------------------|--------------|--------|
| FinBERT | `/api/v1/enhanced-sentiment/analyze` | POST |
| LLaMA 3 | `/api/v1/enhanced-sentiment/analyze-llama` | POST |
| Consensus (FinBERT + LLaMA) | `/api/v1/enhanced-sentiment/analyze-consensus` | POST |
| LightGBM Signals | `/api/v1/trading-signals/generate` | POST |
| WebSocket stream | `ws://<host>:8004` | JSON |

No code changes required – just make sure **both the main API and this stack are up** (either by:

1. Running two separate compose files, or  
2. Copying these services into the root-level `docker-compose.yml`).

---

## 7 .  Common Tasks

### 7.1  Train & mount a real LightGBM model

```python
# train_lgbm.py (example)
import lightgbm as lgb, joblib
model = lgb.train(params, lgb.Dataset(X_train, label=y_train))
joblib.dump(model, "lgbm_model.pkl")
```

```
ml_services/signal_generator/model/lgbm_model.pkl
docker compose up --build signal_generator
```

### 7.2  Add your own TFT checkpoint

Place `tft_best.ckpt` in `ml_services/price_forecast_service/model/`  
and rebuild `price_forecast_service`.

### 7.3  Scale FinBERT horizontally

```bash
docker compose up --scale sentiment_service=3 -d
```

Use a load balancer (Traefik / Nginx) or update gateway code to round-robin.

---

## 8 .  Deploying on Google Cloud

| Component | GCP Service | Notes |
|-----------|-------------|-------|
| CPU services (FinBERT, LightGBM) | **Cloud Run** | zero-ops, auto-scale |
| GPU service (LLaMA 3) | **GKE** node pool with T4/L4 GPUs | use node taints |
| Redis | **Memorystore** | serverless |
| Images | **Artifact Registry** | `gcloud builds submit` |
| Monitoring | **Cloud Monitoring & Logging** | out-of-the-box with Ops Agent |

1. Build images locally or via Cloud Build.  
2. Push to Artifact Registry.  
3. Deploy each service with the matching CPU/GPU template.  

---

## 9 .  Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `llama3_sentiment_service` exits instantly | No GPU / NVIDIA driver missing | Comment out service or install driver |
| `redis: Connection refused` | Redis container not ready | `docker compose up redis`, then retry |
| WebSocket clients disconnect | Proxy / firewall blocking 8004 | Expose port or use Nginx WebSocket upgrade |
| `ModuleNotFoundError: pytorch_forecasting` | TFT service dependency mismatch | Rebuild with `--build` |

---

## 10 .  Security Notes

* The stack is **demo-grade** (no TLS, no auth).  
* Put the services behind an API gateway & secure network in production.  
* Mount checkpoint directories **read-only** in production to avoid tampering.

---

## 11 .  Cleaning Up

```bash
docker compose down -v --remove-orphans
# Remove images
docker images "nexussentinel*" -q | xargs docker rmi
```

---

Happy shipping 🚀
