# NexusSentinel Auto-Trader

Hands-free order executor that **listens to NexusSentinel’s real-time trading-signal
WebSocket** and places BUY / SELL orders on Alpaca (**paper or live**) according
to configurable rules.

---

## 1  How It Works ⚙️

| Step | Component | Description |
|------|-----------|-------------|
| 1 | WebSocket Signal Server (`ws://websocket_signal_server:8004`) | Streams JSON trading-signals from LightGBM/FinBERT/LLaMA pipeline |
| 2 | **Auto-Trader (main.py)** | Persistent async client<br>· Keeps WS connection alive with heartbeats<br>· Parses messages of type `signal` |
| 3 | Decision Engine | Discards signals with `confidence < CONFIDENCE_THRESHOLD` (default 0.70) |
| 4 | Trade Executor | Depending on **TRADE_MODE**<br>  • `auto` → submits order via Alpaca REST<br>  • `manual` → only logs signal |
| 5 | REST API (`api.py`) | Exposes `/account`, `/positions`, `/trades`, `/set-mode`, `/manual-trade` for the Streamlit dashboard |
| 6 | Logging & Retry | Tenacity retry wrapper (exponential back-off, default 3 attempts) – rate-limit & transient errors are re-tried automatically. Every executed order is appended to `trade_history.json` (persisted on graceful shutdown). |

### Signal JSON schema

```json
{
  "type": "signal",
  "symbol": "TSLA",
  "action": "BUY",      // BUY | SELL | HOLD
  "confidence": 0.91,
  "timestamp": "2025-06-20T14:30:12"
}
```

---

## 2  Configuration 🛠️

All parameters are loaded from `ml_services/auto_trader/.env` (see
`.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ALPACA_API_KEY` / `ALPACA_API_SECRET` | – | Obtain from [Alpaca](https://alpaca.markets/) |
| `ALPACA_BASE_URL` | `https://paper-api.alpaca.markets` | Switch to live URL for live trading |
| `WEBSOCKET_URL` | `ws://websocket_signal_server:8004` | Internal docker-compose host |
| `TRADE_MODE` | `manual` | `manual` or `auto` |
| `CONFIDENCE_THRESHOLD` | `0.7` | Minimum confidence to act on a signal |
| `DEFAULT_QUANTITY` | `1` | Shares per trade (can be overridden in REST call) |
| `MAX_RETRIES` | `3` | Tenacity retry attempts for Alpaca errors |
| `HEARTBEAT_INTERVAL` | `30` | Seconds between WS ping messages |
| `LOG_LEVEL` | `INFO` | Standard Python log level |

---

## 3  Trading Modes 🔄

| Mode | Behaviour | How to switch |
|------|-----------|---------------|
| **manual** (*safe default*) | Signals are **only logged** & forwarded to dashboard. Use `/manual-trade` or dashboard button to execute. | 1. Set `TRADE_MODE=manual` in `.env` **or** 2. `POST /set-mode {"mode":"manual"}` |
| **auto** | Order is submitted to Alpaca instantly once confidence ≥ threshold. | 1. `TRADE_MODE=auto` **or** 2. `POST /set-mode {"mode":"auto"}` (Dashboard radio) |

---

## 4  Running 🚀

### 4.1 Docker-Compose (recommended)

Auto-Trader is already defined in the root `docker-compose.yml`:

```bash
# copy secrets
cp ml_services/auto_trader/.env.example ml_services/auto_trader/.env
# edit Alpaca keys + mode ...
docker compose up auto_trader
```

The container launches **both** the REST API (port 8000) **and** the WS client.

### 4.2 Standalone (local dev)

```bash
pip install -r ml_services/auto_trader/requirements.txt
export $(cat ml_services/auto_trader/.env | xargs)   # load env vars
python ml_services/auto_trader/main.py               # WS client
# in another terminal
uvicorn ml_services/auto_trader/api:app --reload
```

---

## 5  REST API Endpoints (8000)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Module health incl. Alpaca connectivity |
| `GET` | `/account` | Equity, cash, buying power, status |
| `GET` | `/positions` | Current open positions |
| `GET` | `/trades` | Persisted trade history (JSON) |
| `GET` | `/mode` | Current trading mode |
| `POST` | `/set-mode` `{"mode":"auto|manual"}` | Toggle trading mode |
| `POST` | `/manual-trade` | Manually submit BUY/SELL (only accepted in manual mode) |
| `POST` | `/auto-trade` | Programmatic trade endpoint for other services |

All responses are JSON; errors return HTTP 4xx/5xx with detail message.

---

## 6  Error Handling & Resilience 🛡️

* **Tenacity** wraps Alpaca calls – automatic retries with exponential back-off
  (1 s → 4 s → 16 s … up to `MAX_RETRIES`).
* **RateLimitException** & temporary network issues are retried automatically.
* Every successful/failed order is logged to `auto_trader.log`.
* Trade metadata is appended to `trade_history.json` **before shutdown** (SIGINT/SIGTERM handler).
* WS connection auto-reconnects with back-off (1 s → 2 s → 4 s … 60 s max).
* Heartbeat ping/pong keeps long-lived WS connections alive behind firewalls.

---

## 7  Security & Safety 🔒

1. **Use Paper Trading** while testing (`ALPACA_BASE_URL=https://paper-api.alpaca.markets`).
2. Never commit `.env` with live keys. Use secrets-manager in prod.
3. Consider position sizing / risk limits – `DEFAULT_QUANTITY` is a placeholder.
4. Add additional checks (market status, circuit breakers) before order submission in `process_signal()`.

---

## 8  Extending

* **Advanced risk-management**: integrate notional exposure limits per symbol.
* **OCO / bracket orders**: switch `type="market"` to `limit`/`stop` with TP/SL.
* **Multi-account routing**: create separate REST resources to fan-out to several Alpaca accounts.
* **Back-testing harness**: feed historical signals into the module with `TRADE_MODE=manual` to record hypothetical P/L.

---

Happy (safe) trading! 🚀
