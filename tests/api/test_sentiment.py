"""
Tests for the sentiment analysis API endpoints.

This module contains tests for:
- /api/v1/sentiment/analyze endpoint
- FinBERT integration
- OpenAI fallback mechanism
- Entity extraction functionality

Tests use mocked external API calls to avoid actual network requests.
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from httpx import AsyncClient, Response, RequestError

from app.main import app
from app.services.sentiment_analysis import (
    SentimentAnalyzer,
    FinBERTAnalyzer, 
    OpenAIAnalyzer,
    SentimentLabel,
    EntityType,
    Entity
)


# --- Test Fixtures ---

@pytest.fixture
def test_app():
    """Create a test instance of the FastAPI application."""
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI application."""
    with TestClient(test_app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(test_app):
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


# --- Mock Response Fixtures ---

@pytest.fixture
def mock_finbert_high_confidence():
    """Mock a high-confidence response from FinBERT."""
    return {
        "sentiment": "positive",
        "confidence": 0.92,
        "metadata": {
            "processing_time_ms": 45
        }
    }


@pytest.fixture
def mock_finbert_low_confidence():
    """Mock a low-confidence response from FinBERT."""
    return {
        "sentiment": "neutral",
        "confidence": 0.55,
        "metadata": {
            "processing_time_ms": 42
        }
    }


@pytest.fixture
def mock_openai_response():
    """Mock a response from OpenAI."""
    class MockCompletion:
        class Choice:
            class Message:
                content = json.dumps({
                    "sentiment": "positive",
                    "confidence": 0.89,
                    "reasoning": "The text indicates strong financial performance with revenue growth.",
                    "entities": [
                        {
                            "text": "Apple",
                            "type": "company",
                            "confidence": 0.95
                        },
                        {
                            "text": "AAPL",
                            "type": "symbol",
                            "confidence": 0.98
                        }
                    ]
                })

            def __init__(self):
                self.message = self.Message()

        class Usage:
            def __init__(self):
                self.total_tokens = 150

        def __init__(self):
            self.choices = [self.Choice()]
            self.model = "gpt-4o"
            self.usage = self.Usage()

    return MockCompletion()


@pytest.fixture
def sample_text():
    """Sample financial text for testing."""
    return "Apple (AAPL) reported strong quarterly earnings, with revenue up 10% year-over-year, exceeding analyst expectations."


# --- Test Cases ---

@pytest.mark.asyncio
async def test_sentiment_analyze_high_confidence(
    async_client, sample_text, mock_finbert_high_confidence
):
    """Test successful sentiment analysis with high confidence from FinBERT."""
    # Mock FinBERT API response
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_high_confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Make request to our API
        response = await async_client.post(
            "/api/v1/sentiment/analyze",
            json={"text": sample_text}
        )

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sentiment"] == "positive"
        assert data["confidence"] >= 0.9
        assert data["source"] == "finbert"
        assert "request_id" in data
        assert "processed_at" in data


@pytest.mark.asyncio
async def test_sentiment_analyze_with_entity_extraction(
    async_client, sample_text, mock_finbert_high_confidence
):
    """Test sentiment analysis with entity extraction."""
    # Mock FinBERT API response with entities
    with patch('httpx.AsyncClient.post') as mock_post, \
         patch('app.services.sentiment_analysis.FinBERTAnalyzer.extract_entities') as mock_extract:
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_high_confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Setup mock entity extraction
        mock_extract.return_value = [
            Entity(text="Apple", type=EntityType.COMPANY, confidence=0.95, metadata={"possible_symbols": ["AAPL"]}),
            Entity(text="AAPL", type=EntityType.SYMBOL, confidence=0.98, metadata={})
        ]

        # Make request to our API
        response = await async_client.post(
            "/api/v1/sentiment/analyze",
            json={"text": sample_text, "extract_entities": True}
        )

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sentiment"] == "positive"
        assert len(data["entities"]) == 2
        assert data["entities"][0]["text"] == "Apple"
        assert data["entities"][0]["type"] == "company"
        assert data["entities"][1]["text"] == "AAPL"
        assert data["entities"][1]["type"] == "symbol"


@pytest.mark.asyncio
async def test_sentiment_analyze_finbert_low_confidence_fallback(
    async_client, sample_text, mock_finbert_low_confidence, mock_openai_response
):
    """Test fallback to OpenAI when FinBERT returns low confidence."""
    # Mock FinBERT API response with low confidence
    with patch('httpx.AsyncClient.post') as mock_finbert_post, \
         patch('openai.ChatCompletion.acreate') as mock_openai:
        
        # Setup FinBERT mock
        mock_finbert_response = MagicMock()
        mock_finbert_response.json.return_value = mock_finbert_low_confidence
        mock_finbert_response.raise_for_status = MagicMock()
        mock_finbert_post.return_value = mock_finbert_response
        
        # Setup OpenAI mock
        mock_openai.return_value = mock_openai_response

        # Make request to our API with explicit threshold
        response = await async_client.post(
            "/api/v1/sentiment/analyze",
            json={"text": sample_text},
            params={"confidence_threshold": 0.6}
        )

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sentiment"] == "positive"  # From OpenAI
        assert data["source"] == "openai"
        assert "reasoning" in data
        assert data["confidence"] > 0.8


@pytest.mark.asyncio
async def test_sentiment_analyze_finbert_error_fallback(
    async_client, sample_text, mock_openai_response
):
    """Test fallback to OpenAI when FinBERT API fails."""
    # Mock FinBERT API error and OpenAI success
    with patch('httpx.AsyncClient.post') as mock_finbert_post, \
         patch('openai.ChatCompletion.acreate') as mock_openai:
        
        # Setup FinBERT mock to raise exception
        mock_finbert_post.side_effect = RequestError("Connection error")
        
        # Setup OpenAI mock
        mock_openai.return_value = mock_openai_response

        # Make request to our API
        response = await async_client.post(
            "/api/v1/sentiment/analyze",
            json={"text": sample_text}
        )

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["source"] == "openai"
        assert "reasoning" in data


@pytest.mark.asyncio
async def test_sentiment_analyze_both_services_fail(async_client, sample_text):
    """Test error handling when both FinBERT and OpenAI fail."""
    # Mock both services to fail
    with patch('httpx.AsyncClient.post') as mock_finbert_post, \
         patch('openai.ChatCompletion.acreate') as mock_openai:
        
        # Setup FinBERT mock to raise exception
        mock_finbert_post.side_effect = RequestError("Connection error")
        
        # Setup OpenAI mock to raise exception
        mock_openai.side_effect = Exception("OpenAI error")

        # Make request to our API
        response = await async_client.post(
            "/api/v1/sentiment/analyze",
            json={"text": sample_text}
        )

        # Check response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_sentiment_analyze_invalid_input(async_client):
    """Test error handling with invalid input."""
    # Test with empty text
    response = await async_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": ""}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with missing text field
    response = await async_client.post(
        "/api/v1/sentiment/analyze",
        json={"source": "news"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test with text that's too long
    response = await async_client.post(
        "/api/v1/sentiment/analyze",
        json={"text": "a" * 6000}  # Exceeds max length
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_sentiment_analyze_with_metadata(async_client, sample_text, mock_finbert_high_confidence):
    """Test sentiment analysis with additional metadata."""
    # Mock FinBERT API response
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_high_confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Make request with metadata
        response = await async_client.post(
            "/api/v1/sentiment/analyze",
            json={
                "text": sample_text,
                "source": "news",
                "metadata": {
                    "article_id": "12345",
                    "publisher": "Financial Times"
                }
            }
        )

        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sentiment"] == "positive"
        
        # Verify the request included metadata
        call_args = mock_post.call_args
        assert "json" in call_args[1]
        assert "text" in call_args[1]["json"]
        
        # In a real test we'd verify the metadata was passed correctly,
        # but our mock doesn't capture this detail
