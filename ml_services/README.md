# NexusSentinel ‒ ML Services Suite

This document explains the purpose, interfaces, and interactions of the standalone machine-learning micro-services that power advanced sentiment and trading-signal features in **NexusSentinel**.  
All services live under the `ml_services/` directory and are shipped as independent Docker images so they can be developed, tested, and scaled in isolation.

---

## 1. High-level Architecture

```
+--------------+        REST / WebSocket       +--------------------+
|  React App   |  ───────────────────────────► |  FastAPI Gateway    |
|  (frontend)  |                               |  nexus/api          |
+--------------+                               +---------┬----------+
                                                          │
                             ┌────────────────────────────┼────────────────────────────┐
                             │                            │                            │
                  /sentiment │                /llama-sentiment                /signal │
            +----------------------+   +---------------------------+   +-----------------------+
            | sentiment_service    |   | llama3_sentiment_service  |   |  signal_generator     |
            |  (FinBERT + Redis)   |   |  (LLaMA-3-8B quantized)   |   | (LightGBM / fallback) |
            +----------┬-----------+   +-------------┬-------------+   +-----------┬-----------+
                       │ Redis (cache)               │ GPU          └──────────────┘
                       └───────────────┬─────────────┘
                                       │
                                Optional future:
                                price_forecast_service (TFT)
```

* **Gateway**  
  Your existing monolithic FastAPI app (`app/`) now exposes new proxy routes under `/api/v1/enhanced-sentiment` and `/api/v1/trading-signals`. The gateway handles authentication, orchestration, and response aggregation.

* **sentiment_service** – Fast, FinBERT-based financial tone classification. Uses Redis to cache the most recent inferences (1 h TTL) for sub-millisecond repeat hits.

* **llama3_sentiment_service** – Deeper, context-aware sentiment via LLaMA-3-8B (8-bit). Runs on GPU; slower but better at sarcasm, idioms, and long-form text.

* **signal_generator** – Converts combined sentiment & technical features into trading actions using a trained LightGBM model (falls back to a rule-based dummy model when no `.pkl` present).

* **price_forecast_service** *(optional)* – Houses a Temporal-Fusion-Transformer for multi-horizon price prediction. Not yet wired into compose but left as a placeholder.

---

## 2. Service Catalogue

| Service Dir | Container Port | Key Endpoint | Purpose | Dependencies |
|-------------|---------------|--------------|---------|--------------|
| `sentiment_service` | `8000` | `POST /sentiment` | FinBERT sentiment (positive / neutral / negative + confidence) | Redis |
| `llama3_sentiment_service` | `8001` | `POST /llama-sentiment` | Nuanced sentiment with LLaMA 3 | NVIDIA GPU, bitsandbytes |
| `signal_generator` | `8002` | `POST /signal` | Outputs `STRONG_BUY … STRONG_SELL` with probability | Trained `model/lgbm_model.pkl` (optional) |
| `price_forecast_service` | `8003`* | `POST /forecast` | Price/time-series forecasting (TFT) | PyTorch Forecasting |

\*  Port is illustrative; change when service is added.

---

## 3. Data Flow

1. **Frontend** submits a symbol or free-form text to `/enhanced-sentiment/*` on the gateway.  
2. Gateway forwards to:
   - FinBERT (`sentiment_service`) **and/or**
   - LLaMA (`llama3_sentiment_service`)
3. Gateway merges results (weighted consensus) and returns enriched sentiment JSON.
4. `/trading-signals/stock/{symbol}` endpoint:
   - Fetches consensus sentiment (step 2)
   - Retrieves technicals (RSI, volume, etc.) from market data adapters
   - Sends feature vector to `signal_generator`
   - Returns action + confidence to frontend and alerting engine.

---

## 4. Running Locally

```
# 1. Build and start everything (DB, API, ML, Redis)
docker compose up --build

# 2. Hit health checks
curl localhost:8000/health                     # main API
curl localhost:8003/enhanced-sentiment/health  # proxy -> FinBERT / LLaMA
curl localhost:8002/signal_generator/health    # signal service
```

### GPU notes
`llama3_sentiment_service` is built FROM `nvidia/cuda:12.2*` and requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/) on the host.

---

## 5. Google Cloud Deployment

| Component | Recommended GCP Service |
|-----------|-------------------------|
| API Gateway (monolith) | Cloud Run or GKE (standard node) |
| FinBERT service | Cloud Run (CPU) |
| LLaMA service | GKE node pool with NVIDIA T4 / L4 GPUs |
| Signal generator | Cloud Run (CPU) |
| Redis | Memorystore for Redis |
| Container Registry | Artifact Registry |
| Observability | Cloud Logging & Cloud Monitoring |

The repo’s `docker-compose.yml` mirrors this topology; a Terraform or Helm chart can map 1-to-1 to GCP resources.

---

## 6. Development Tips

1. **Hot-reload** inside a service:  
   ```bash
   docker compose exec sentiment_service \
       uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **Swap dummy → real LightGBM**: drop a `lgbm_model.pkl` into `ml_services/signal_generator/model/` and rebuild the container.
3. **Experiment quickly**: Each service is <50 lines to spin up. Clone, tweak `requirements.txt`, run `docker compose up --build service_name`.

---

## 7. Extending the Suite

| Idea | Where to Plug-In |
|------|------------------|
| Triton Inference Server for dynamic batching | Replace individual model containers |
| Prometheus metrics | Add `/metrics` endpoint via `fastapi_prometheus` |
| Kafka or ZeroMQ stream | `infra_redis_zmq/` service (not yet committed) |
| Edge deployment | Quantize FinBERT using ONNX + `optimum` |

---

### Contributing

1. PR to `feature/ml-service-x`.
2. Update this README with new service description / port.
3. Run `make compose-test` (CI) before merging to `main`.

Happy shipping! 🚀
