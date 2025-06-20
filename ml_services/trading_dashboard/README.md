# NexusSentinel Trading Dashboard 📈

A Streamlit-powered web UI (port **8501**) that lets you **watch live ML trading signals, toggle AUTO ⇆ MANUAL mode, and execute trades with one click**.

---

## 1  Boot & Access

```bash
# run entire stack
docker compose up trading_dashboard auto_trader  # dashboard + backend

# open in browser
http://localhost:8501
```

If you are developing outside Docker:

```bash
cd ml_services/trading_dashboard
pip install -r requirements.txt
streamlit run app.py
```

> Environment variables (`API_URL`, `WEBSOCKET_URL`, `AUTO_TRADER_API`) default to internal
> docker-compose hostnames.  
> Override them in `.env` or `export` before launching for local dev.

---

## 2  Feature Tour

```
╭───────────────────────── NexusSentinel Dashboard ─────────────────────────╮
│  📈  Live Signals (Tab)            📝 Positions & History       📊 Market │
├────────────────────────────────────────────────────────────────────────────┤
│ 🔄 Mode Switch [ Manual ☐  Auto ☐ ]                                       │
│ ────────────────────────────────────────────────────────────────────────── │
│ 🔔  TSLA → BUY  Confidence: 0.91   [Execute BUY]                           │
│ 🔔  AAPL → SELL Confidence: 0.88   [Execute SELL]                          │
│ …                                                                         │
│ ────────────────────────────────────────────────────────────────────────── │
│ 💰 Equity      $101 234.56     💵 Cash    $22 345.67                       │
│ 🟢 Connected to Signal Server                                             │
╰────────────────────────────────────────────────────────────────────────────╯
```

| Section | Description |
|---------|-------------|
| **Sidebar** | Mode toggle; account equity chart; connection health |
| **📊 Live Signals** | Real-time feed from WebSocket – expands to show technical indicators & sentiment details. In **Manual** mode every card has an **Execute** button. |
| **📝 Positions & History** | Open positions (table + pie), executed trades log (sortable, downloadable). |
| **📈 Market Overview** | Top movers, aggregated sentiment bar, and recent news headlines. |

### Hot-Reload

Streamlit auto-reloads when code changes.  
When *Auto-refresh* is ticked, the Live Signals tab refreshes every **5 s**.

---

## 3  Trading Modes

| Mode | Behaviour | Visual Cue |
|------|-----------|------------|
| 👨‍💻 **Manual** | Signals are displayed, no order is sent until you press **Execute**. | Sidebar badge **MANUAL** |
| 🤖 **Auto** | Orders dispatched instantly via Auto-Trader once `confidence ≥ 0.70`. | Sidebar badge **AUTO** turns orange & modal warning |

Switching calls `POST /set-mode` on the Auto-Trader REST API.

---

## 4  Customization Guide

| Want to… | Edit / Override |
|----------|-----------------|
| Change the confidence threshold label colour | `app.py` → `if signal['confidence'] > …` |
| Feed real market movers / news | Replace placeholder lists in *Market Overview* with API calls (e.g. Finnhub, Polygon). |
| Add new technical columns | Update `technicals` rendering loop in `Live Signals` expander. |
| Limit displayed signals | Tweak `st.session_state.signals[:N]` slice. |
| Theme / CSS tweaks | Add a `config.toml` or use Streamlit theme settings. |

#### Environment Variables

```env
API_URL=http://localhost:8000           # FastAPI gateway
WEBSOCKET_URL=ws://localhost:8004       # Signal stream
AUTO_TRADER_API=http://localhost:8000   # Auto-Trader REST (inside same container)
```

Export or prefix `docker compose`:

```bash
WEBSOCKET_URL=ws://127.0.0.1:8004 docker compose up trading_dashboard
```

---

## 5  Screenshots

*(PNG files live in `docs/img/`; ASCII approximation above for GitHub markdown)*

| Live Signals | Positions | Mode Toggle |
|--------------|-----------|-------------|
| ![signals](../../docs/img/dashboard_signals.png) | ![positions](../../docs/img/dashboard_positions.png) | ![toggle](../../docs/img/dashboard_toggle.png) |

---

## 6  Troubleshooting

| Symptom | Fix |
|---------|-----|
| **“Disconnected from Signal Server”** | Ensure `websocket_signal_server` is running & port 8004 is exposed. |
| **Buttons do nothing in AUTO mode** | Manual execution is disabled – switch back to Manual. |
| **Account info blank** | Check Auto-Trader REST (`curl :8000/health`) and Alpaca credentials. |
| **Dashboard won’t load external JS/CSS** | Some corporate proxies block Streamlit WebSocket – add `--server.enableWebsocketCompression false`. |

---

## 7  Roadmap

* Editable position sizing per trade  
* Notification sounds / desktop alerts  
* Dark-mode theme & mobile-first layout  
* Historical signal replay / back-test visualizer  

Pull requests welcome — enjoy trading with NexusSentinel! 🛸
