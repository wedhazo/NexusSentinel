# NexusSentinel

*(existing README content above remains unchanged)*

---

## Sentiment Analysis API

NexusSentinel now ships with a dedicated, production-ready sentiment-analysis service designed for finance-specific text.  
The service provides fast, specialized inference via FinBERT/FinGPT **with automatic fallback to OpenAI GPT-4o/4** whenever additional accuracy or low-confidence recovery is required.

### 1. Endpoint

```
POST /api/v1/sentiment/analyze
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✓ | Raw text to analyse (≤ 5 000 chars). |
| `source` | string | – | Optional text origin, e.g. `news`, `twitter`, `reddit`. |
| `extract_entities` | bool | – | Defaults to `true`. Toggle entity extraction. |
| `metadata` | object | – | Arbitrary key/value payload forwarded to upstream provider. |

Query param  
`confidence_threshold` – override global fallback threshold (default = `0.6`).

### 2. Dual-Provider Architecture

```
┌─────────────┐     high-confidence (≥ threshold) ──────────► Return
│  FinBERT /  │
│   FinGPT    │──── low-confidence (< threshold) ─►┐
└─────────────┘                                   │
                                                  ▼
                                          ┌─────────────┐
                                          │   OpenAI    │
                                          │ GPT-4o | 4  │
                                          └─────────────┘
```

1. Primary request is sent to a configurable FinBERT/FinGPT endpoint (FinBrain, FinGPT, or custom).
2. If the response confidence is **below the threshold** *or* the provider fails, the same text is re-routed to OpenAI ChatGPT (`gpt-4o`; fallback `gpt-4`).
3. The chosen provider is reflected in the response’s `source` field (`"finbert"` or `"openai"`).

### 3. Entity Extraction

When `extract_entities=true`, NexusSentinel returns a lightweight list of recognised financial entities:

```json
"entities": [
  {
    "text": "Apple",
    "type": "company",
    "confidence": 0.95,
    "metadata": { "possible_symbols": ["AAPL"] }
  },
  {
    "text": "AAPL",
    "type": "symbol",
    "confidence": 0.98,
    "metadata": {}
  }
]
```

Supported `type` values: `company`, `symbol`, `financial_instrument`, `other`.

### 4. Required Configuration

Add the following variables to `.env` (see **app/config.py** for defaults):

```
# FinBERT / FinGPT
FINBERT_API_KEY=your_key
FINBERT_API_URL=https://api.finbrain.tech/v1/sentiment   # or FinGPT/custom
FINBERT_PROVIDER=finbrain                                # finbrain | fingpt | custom
FINBERT_AUTH_METHOD=api-key                              # api-key | bearer | custom

# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
OPENAI_FALLBACK_MODEL=gpt-4

# Fallback logic
SENTIMENT_CONFIDENCE_THRESHOLD=0.6
```

Docker/Cloud Run automatically picks these up from Secret Manager or `.env`.

### 5. Quick Test

```bash
curl -X POST http://localhost:8000/api/v1/sentiment/analyze \
     -H "Content-Type: application/json" \
     -d '{
           "text": "Tesla (TSLA) shares rally after record delivery numbers.",
           "source": "news"
         }'
```

### 6. Sample Response

```json
{
  "text": "Tesla (TSLA) shares rally after record delivery numbers.",
  "sentiment": "positive",
  "confidence": 0.93,
  "source": "finbert",
  "reasoning": "The headline signals strong performance likely to uplift investor sentiment.",
  "entities": [
    { "text": "Tesla", "type": "company", "confidence": 0.94, "metadata": { "possible_symbols": ["TSLA"] } },
    { "text": "TSLA",  "type": "symbol",  "confidence": 0.98, "metadata": {} }
  ],
  "metadata": {
    "processing_time_ms": 123,
    "provider": "finbrain"
  },
  "request_id": "1c5c0e29-d9bf-40e9-95b3-e5b94996ac8c",
  "processed_at": "2025-06-14T12:34:56.789Z"
}
```

### 7. Running Tests

```bash
# Unit & integration tests (incl. mocked FinBERT/OpenAI)
pytest tests/api/test_sentiment.py -q
```

The test-suite mocks external calls, validating:
* high-confidence FinBERT path
* low-confidence fallback to OpenAI
* entity extraction correctness
* graceful error handling

---

*Happy coding & insightful sentiment tracking!*  
For questions or issues, open a GitHub Discussion or email **support@nexussentinel.dev**.
