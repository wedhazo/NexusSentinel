"""
Services package for NexusSentinel.

This package contains service modules that provide functionality used across
the application, including:
- Sentiment analysis services (FinBERT/FinGPT and OpenAI integrations)
- Entity extraction for financial text
- Other utility services

Services in this package are designed to be reusable and independent of the API layer.
"""

# Import key functions and classes for easier access
from app.services.sentiment_analysis import (
    analyze_text_sentiment,
    get_sentiment_analyzer,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentLabel,
    EntityType,
    Entity
)

__all__ = [
    'analyze_text_sentiment',
    'get_sentiment_analyzer',
    'SentimentAnalysisRequest',
    'SentimentAnalysisResponse',
    'SentimentLabel',
    'EntityType',
    'Entity',
]
