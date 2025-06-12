# NexusSentinel

Stock-market intelligence & sentiment-analysis platform powered by FastAPI, PostgreSQL and SQLAlchemy.

| Section | Purpose |
|---------|---------|
| [Features](#features) | What NexusSentinel offers |
| [Tech Stack](#tech-stack) | Core technologies |
| [Project Structure](#project-structure) | Important folders & files |
| [Quick Start](#quick-start) | TL;DR to run everything with Docker |
| [Local Development](#local-development) | Manual installation with `pip` |
| [Environment Variables](#environment-variables) | `.env` reference |
| [Database Schema](#database-schema) | Tables & relationships |
| [API Reference](#api-reference) | Endpoints summary |
| [Usage Examples](#usage-examples) | `curl` snippets |
| [Contributing](#contributing) | How to get involved |
| [License](#license) | MIT |

---

## Features
* Unified **stock fundamentals, OHLCV, technicals, news & social sentiment** in one API  
* **Async** FastAPI backend with auto-generated Swagger (`/docs`) & OpenAPI (`/api/v1/openapi.json`)  
* Modular **SQLAlchemy ORM** models (14 tables)  
* **PostgreSQL** with asyncpg, connection-pooling and Alembic migrations  
* **Docker / docker-compose** for zero-friction deployment (optional pgAdmin)  
* Robust **health & metrics** endpoints (`/health`, `/health/detailed`)  
* Built-in **rate limiting**, CORS, configurable logging, `.env` first approach  

---

## Tech Stack
* Python 3.11  
* FastAPI 0.110 / Starlette 0.36  
* SQLAlchemy 2 (async) + asyncpg  
* PostgreSQL 15-alpine  
* Alembic for migrations  
* Uvicorn / Gunicorn (production)  
* Docker & docker-compose (optional)  

---

## Project Structure
```
NexusSentinel/
├─ app/
│  ├─ api/                 # Routers & endpoint modules
│  │  └─ v1/
│  │     ├─ endpoints/
│  │     │   └─ stocks.py
│  │     └─ router.py
│  ├─ models/              # SQLAlchemy models (one file per table)
│  ├─ config.py            # Pydantic Settings
│  ├─ database.py          # Async engine & session
│  └─ main.py              # FastAPI application factory
├─ .env                    # Environment variables (**never commit secrets**)
├─ requirements.txt        # Python dependencies
├─ Dockerfile              # Production image
├─ docker-compose.yml      # API + PostgreSQL (+ pgAdmin)
└─ README.md
```

---

## Quick Start

### 1. Clone & configure
```bash
git clone https://github.com/your-org/NexusSentinel.git
cd NexusSentinel
cp .env .env.local   # customise credentials & secrets
```

### 2. Run with Docker
```bash
docker compose --env-file .env.local up --build
```
Services:  
* `api` → http://localhost:8000  
* `db` → localhost:5432  
* `pgadmin` (only in dev profile) → http://localhost:5050

Stop & remove containers:
```bash
docker compose down -v
```

---

## Local Development (without Docker)

```bash
py -m venv .venv && source .venv/Scripts/activate   # Windows example
python -m pip install -r requirements.txt
cp .env .env.local
# edit .env.local with your DB creds
psql -c "CREATE DATABASE nexussentinel;"            # or use pgAdmin
alembic upgrade head                                # migrations (optional)
python run_server.py --reload                       # http://localhost:8000
```

---

## Environment Variables

| Key | Default | Description |
|-----|---------|-------------|
| `DB_HOST` / `DB_PORT` | localhost / 5432 | PostgreSQL host/port |
| `DB_USER` / `DB_PASSWORD` | postgres / *** | Database credentials |
| `DB_NAME` | nexussentinel | Database name |
| `DATABASE_URL` | derived | Full SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `API_HOST` / `API_PORT` | 0.0.0.0 / 8000 | Uvicorn bind address |
| `SECRET_KEY` | *change me* | JWT / session signing |
| `CORS_ORIGINS` | `http://localhost:3000` | Front-end origins (comma list) |
| `RATE_LIMIT_DEFAULT` | 100 | Requests per period |

_See `.env` for the complete list._

---

## Database Schema

| Table | Purpose / Key Columns |
|-------|-----------------------|
| `stocks_core` | Company fundamentals (`symbol`, `company_name`, `sector` …) |
| `stocks_ohlcv_daily` | Daily OHLCV (`date`, `open`, `close`, `volume`) |
| `stocks_ohlcv_intraday_5min` | 5-minute OHLCV (`timestamp`) |
| `stocks_financial_statements_quarterly` | `fiscal_quarter`, `revenue`, `eps_basic` |
| `stocks_financial_statements_annual` | Annual financials |
| `stocks_technical_indicators_daily` | SMA/EMA, RSI, MACD, etc. |
| `stocks_news` | News articles with `sentiment_score` |
| `stocks_social_posts` | Twitter/Reddit posts with sentiment |
| `stocks_sentiment_daily_summary` | Aggregated daily sentiment |
| `stocks_dividends` | Dividend history (`ex_date`, `amount`) |
| `stocks_splits` | Stock split events |
| `stocks_analyst_ratings` | Analyst ratings & target prices |
| `macro_indicators_lookup` | Master list of macro indicators |
| `macro_economic_data` | Daily/weekly macro values |

Foreign-key relationships are declared in each SQLAlchemy model (`app/models/**.py`) and use `ON DELETE CASCADE` to maintain referential integrity.

---

## API Reference

> Full interactive documentation is auto-generated at **`/docs`** (Swagger UI)  
> Raw schema: **`/api/v1/openapi.json`**

| Method & Path | Description |
|---------------|------------|
| `GET  /api/v1/stocks` | List stocks (filter by sector, search, pagination) |
| `POST /api/v1/stocks` | Create new company record |
| `GET  /api/v1/stocks/{symbol}` | **Comprehensive data** (fundamentals, OHLCV, financials, sentiment, macro) |
| `PUT  /api/v1/stocks/{symbol}` | Update stock fundamentals |
| `DELETE /api/v1/stocks/{symbol}` | Delete stock & cascade children |
| `POST /api/v1/stocks/sentiment` | Submit sentiment result (news / social) |
| `GET  /api/v1/stocks/sentiment/aggregate` | Aggregated sentiment by date & source |
| `GET  /health` | Basic health |
| `GET  /health/detailed` | System & dependency status |

---

## Usage Examples

### 1. Query Full Stock Data
```bash
curl -X GET "http://localhost:8000/api/v1/stocks/AAPL?query_date=2025-05-31" | jq
```

### 2. Submit Sentiment Result
```bash
curl -X POST "http://localhost:8000/api/v1/stocks/sentiment" \
-H "Content-Type: application/json" \
-d '{
  "symbol": "AAPL",
  "date": "2025-06-11",
  "source": "news",
  "sentiment_score": 0.82,
  "sentiment_label": "positive",
  "volume": 3,
  "content_sample": "Apple surprises with new product launch",
  "source_details": {
    "publisher": "Reuters",
    "author": "Jane Doe",
    "url": "https://reut.rs/abcd"
  }
}'
```

### 3. Get Aggregated Sentiment Range
```bash
curl "http://localhost:8000/api/v1/stocks/sentiment/aggregate?symbol=AAPL&start_date=2025-05-01&end_date=2025-05-31&sources=news,twitter"
```

---

## Contributing
1. Fork & clone the repo  
2. Create feature branch (`feat/my-awesome-thing`)  
3. Commit with conventional commits  
4. Run `pytest` & `ruff` (or `flake8`) locally  
5. Submit PR – thank you! 🎉

---

