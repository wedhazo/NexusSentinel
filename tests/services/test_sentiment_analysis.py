"""
Tests for the sentiment analysis service.

This module contains tests for:
- FinBERTAnalyzer class
- OpenAIAnalyzer class
- Fallback functionality
- Entity extraction functionality

Tests use mocked external API calls to avoid actual network requests.
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import openai

from app.services.sentiment_analysis import (
    SentimentAnalyzer,
    FinBERTAnalyzer, 
    OpenAIAnalyzer,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentLabel,
    EntityType,
    Entity,
    analyze_text_sentiment,
    get_sentiment_analyzer
)

# --- Test Fixtures ---

@pytest.fixture
def sample_text():
    """Sample financial text for testing."""
    return "Apple (AAPL) reported strong quarterly earnings, with revenue up 10% year-over-year, exceeding analyst expectations."


@pytest.fixture
def sample_negative_text():
    """Sample negative financial text for testing."""
    return "Tesla (TSLA) shares plummeted 15% after missing delivery targets and reporting significant production delays."


@pytest.fixture
def sample_neutral_text():
    """Sample neutral financial text for testing."""
    return "Federal Reserve maintains current interest rates, as widely expected by market analysts."


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
def mock_finbert_negative():
    """Mock a negative sentiment response from FinBERT."""
    return {
        "sentiment": "negative",
        "confidence": 0.88,
        "metadata": {
            "processing_time_ms": 38
        }
    }


@pytest.fixture
def mock_fingpt_response():
    """Mock a response from FinGPT provider."""
    return {
        "label": "positive",
        "score": 0.87,
        "text": "Apple (AAPL) reported strong quarterly earnings"
    }


@pytest.fixture
def mock_custom_response():
    """Mock a response from a custom provider."""
    return {
        "sentiment_class": "positive",
        "confidence_score": 0.91,
        "processing_info": {
            "time_ms": 67,
            "model_version": "v1.2.3"
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
def mock_openai_negative_response():
    """Mock a negative sentiment response from OpenAI."""
    class MockCompletion:
        class Choice:
            class Message:
                content = json.dumps({
                    "sentiment": "negative",
                    "confidence": 0.92,
                    "reasoning": "The text indicates poor performance with stock price decline.",
                    "entities": [
                        {
                            "text": "Tesla",
                            "type": "company",
                            "confidence": 0.96
                        },
                        {
                            "text": "TSLA",
                            "type": "symbol",
                            "confidence": 0.98
                        }
                    ]
                })

            def __init__(self):
                self.message = self.Message()

        class Usage:
            def __init__(self):
                self.total_tokens = 145

        def __init__(self):
            self.choices = [self.Choice()]
            self.model = "gpt-4o"
            self.usage = self.Usage()

    return MockCompletion()


@pytest.fixture
def mock_openai_fallback_model_response():
    """Mock a response from OpenAI fallback model."""
    class MockCompletion:
        class Choice:
            class Message:
                content = json.dumps({
                    "sentiment": "neutral",
                    "confidence": 0.82,
                    "reasoning": "The text presents factual information without clear positive or negative implications.",
                    "entities": [
                        {
                            "text": "Federal Reserve",
                            "type": "company",
                            "confidence": 0.94
                        }
                    ]
                })

            def __init__(self):
                self.message = self.Message()

        class Usage:
            def __init__(self):
                self.total_tokens = 130

        def __init__(self):
            self.choices = [self.Choice()]
            self.model = "gpt-4"  # Fallback model
            self.usage = self.Usage()

    return MockCompletion()


# --- FinBERTAnalyzer Tests ---

@pytest.mark.asyncio
async def test_finbert_analyzer_init():
    """Test FinBERTAnalyzer initialization."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.test.com/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        mock_settings.FINBERT_TIMEOUT_SECONDS = 10
        
        analyzer = FinBERTAnalyzer()
        
        assert analyzer.api_key == "test_key"
        assert str(analyzer.api_url) == "https://api.test.com/sentiment"
        assert analyzer.provider == "finbrain"
        assert analyzer.timeout == 10
        assert analyzer.auth_header == {"X-API-KEY": "test_key"}


@pytest.mark.asyncio
async def test_finbert_auth_header_methods():
    """Test different authentication methods for FinBERTAnalyzer."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Test bearer auth
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_PROVIDER = "fingpt"
        
        analyzer = FinBERTAnalyzer()
        assert analyzer.auth_header == {"Authorization": "Bearer test_key"}
        
        # Test custom auth with bearer
        mock_settings.FINBERT_PROVIDER = "custom"
        mock_settings.FINBERT_AUTH_METHOD = "bearer"
        
        analyzer = FinBERTAnalyzer()
        assert analyzer.auth_header == {"Authorization": "Bearer test_key"}
        
        # Test custom auth with api-key
        mock_settings.FINBERT_AUTH_METHOD = "api-key"
        mock_settings.FINBERT_AUTH_HEADER = "X-Custom-API-Key"
        
        analyzer = FinBERTAnalyzer()
        assert analyzer.auth_header == {"X-Custom-API-Key": "test_key"}


@pytest.mark.asyncio
async def test_finbert_analyze_sentiment_finbrain(sample_text, mock_finbert_high_confidence):
    """Test FinBERTAnalyzer with FinBrain provider."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_high_confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Create analyzer and request
        analyzer = FinBERTAnalyzer()
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_sentiment
        result = await analyzer.analyze_sentiment(request)
        
        # Verify result
        assert result.text == sample_text
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.confidence == 0.92
        assert result.source == "finbert"
        assert "processing_time_ms" in result.metadata
        assert result.metadata["provider"] == "finbrain"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.finbrain.tech/v1/sentiment"
        assert call_args[1]["json"] == {"text": sample_text}
        assert call_args[1]["headers"] == {"X-API-KEY": "test_key"}


@pytest.mark.asyncio
async def test_finbert_analyze_sentiment_fingpt(sample_text, mock_fingpt_response):
    """Test FinBERTAnalyzer with FinGPT provider."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.fingpt.ai/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "fingpt"
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_fingpt_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Create analyzer and request
        analyzer = FinBERTAnalyzer()
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_sentiment
        result = await analyzer.analyze_sentiment(request)
        
        # Verify result
        assert result.text == sample_text
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.confidence == 0.87
        assert result.source == "finbert"
        assert "processing_time_ms" in result.metadata
        assert result.metadata["provider"] == "fingpt"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.fingpt.ai/v1/sentiment"
        assert call_args[1]["json"] == {"text": sample_text, "model": "sentiment"}


@pytest.mark.asyncio
async def test_finbert_analyze_sentiment_custom(sample_text, mock_custom_response):
    """Test FinBERTAnalyzer with custom provider."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.custom.com/sentiment"
        mock_settings.FINBERT_PROVIDER = "custom"
        mock_settings.FINBERT_AUTH_METHOD = "api-key"
        mock_settings.FINBERT_AUTH_HEADER = "X-API-KEY"
        mock_settings.FINBERT_LABEL_FIELD = "sentiment_class"
        mock_settings.FINBERT_CONFIDENCE_FIELD = "confidence_score"
        mock_settings.FINBERT_POSITIVE_LABEL = "positive"
        mock_settings.FINBERT_NEUTRAL_LABEL = "neutral"
        mock_settings.FINBERT_NEGATIVE_LABEL = "negative"
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_custom_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Create analyzer and request
        analyzer = FinBERTAnalyzer()
        request = SentimentAnalysisRequest(
            text=sample_text, 
            extract_entities=False,
            metadata={"custom_param": "value"}
        )
        
        # Call analyze_sentiment
        result = await analyzer.analyze_sentiment(request)
        
        # Verify result
        assert result.text == sample_text
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.confidence == 0.91
        assert result.source == "finbert"
        assert "processing_time_ms" in result.metadata
        assert result.metadata["provider"] == "custom"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.custom.com/sentiment"
        assert "text" in call_args[1]["json"]
        assert call_args[1]["json"]["custom_param"] == "value"


@pytest.mark.asyncio
async def test_finbert_analyze_sentiment_error_handling():
    """Test error handling in FinBERTAnalyzer."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Configure mock to raise exception
        mock_post.side_effect = httpx.RequestError("Connection error")
        
        # Create analyzer and request
        analyzer = FinBERTAnalyzer()
        request = SentimentAnalysisRequest(text="Test text", extract_entities=False)
        
        # Call analyze_sentiment and expect exception
        with pytest.raises(httpx.RequestError):
            await analyzer.analyze_sentiment(request)


@pytest.mark.asyncio
async def test_finbert_extract_entities(sample_text):
    """Test entity extraction in FinBERTAnalyzer."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Create analyzer
        analyzer = FinBERTAnalyzer()
        
        # Call extract_entities
        entities = await analyzer.extract_entities(sample_text)
        
        # Verify entities
        assert len(entities) >= 2  # At least Apple and AAPL
        
        # Find specific entities
        apple_entity = next((e for e in entities if e.text == "Apple"), None)
        aapl_entity = next((e for e in entities if e.text == "AAPL"), None)
        
        assert apple_entity is not None
        assert apple_entity.type == EntityType.COMPANY
        assert apple_entity.confidence > 0
        
        assert aapl_entity is not None
        assert aapl_entity.type == EntityType.SYMBOL
        assert aapl_entity.confidence > 0


# --- OpenAIAnalyzer Tests ---

@pytest.mark.asyncio
async def test_openai_analyzer_init():
    """Test OpenAIAnalyzer initialization."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('app.services.sentiment_analysis.openai') as mock_openai:
        
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_FALLBACK_MODEL = "gpt-4"
        mock_settings.OPENAI_MAX_TOKENS = 500
        mock_settings.OPENAI_TEMPERATURE = 0.1
        
        analyzer = OpenAIAnalyzer()
        
        assert analyzer.api_key == "test_openai_key"
        assert analyzer.model == "gpt-4o"
        assert analyzer.fallback_model == "gpt-4"
        assert analyzer.max_tokens == 500
        assert analyzer.temperature == 0.1
        assert mock_openai.api_key == "test_openai_key"


@pytest.mark.asyncio
async def test_openai_analyze_sentiment(sample_text, mock_openai_response):
    """Test OpenAIAnalyzer sentiment analysis."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Configure mock response
        mock_acreate.return_value = mock_openai_response
        
        # Create analyzer and request
        analyzer = OpenAIAnalyzer()
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=True)
        
        # Call analyze_sentiment
        result = await analyzer.analyze_sentiment(request)
        
        # Verify result
        assert result.text == sample_text
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.confidence == 0.89
        assert result.source == "openai"
        assert result.reasoning == "The text indicates strong financial performance with revenue growth."
        assert "processing_time_ms" in result.metadata
        assert result.metadata["model"] == "gpt-4o"
        assert result.metadata["tokens_used"] == 150
        
        # Verify entities
        assert len(result.entities) == 2
        
        apple_entity = next((e for e in result.entities if e.text == "Apple"), None)
        aapl_entity = next((e for e in result.entities if e.text == "AAPL"), None)
        
        assert apple_entity is not None
        assert apple_entity.type == EntityType.COMPANY
        assert apple_entity.confidence == 0.95
        
        assert aapl_entity is not None
        assert aapl_entity.type == EntityType.SYMBOL
        assert aapl_entity.confidence == 0.98
        
        # Verify API call
        mock_acreate.assert_called_once()
        call_args = mock_acreate.call_args
        assert call_args[1]["model"] == "gpt-4o"
        assert len(call_args[1]["messages"]) == 2
        assert call_args[1]["messages"][0]["role"] == "system"
        assert call_args[1]["messages"][1]["role"] == "user"
        assert call_args[1]["messages"][1]["content"] == sample_text


@pytest.mark.asyncio
async def test_openai_model_fallback(sample_neutral_text, mock_openai_fallback_model_response):
    """Test OpenAIAnalyzer fallback to secondary model."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_FALLBACK_MODEL = "gpt-4"
        
        # Configure mock to raise exception for primary model then succeed for fallback
        def side_effect(*args, **kwargs):
            if kwargs["model"] == "gpt-4o":
                raise openai.error.InvalidRequestError("Model not available", "model")
            else:
                return mock_openai_fallback_model_response
        
        mock_acreate.side_effect = side_effect
        
        # Create analyzer and request
        analyzer = OpenAIAnalyzer()
        request = SentimentAnalysisRequest(text=sample_neutral_text, extract_entities=True)
        
        # Call analyze_sentiment
        result = await analyzer.analyze_sentiment(request)
        
        # Verify result uses fallback model
        assert result.sentiment == SentimentLabel.NEUTRAL
        assert result.source == "openai"
        assert result.metadata["model"] == "gpt-4"
        
        # Verify API was called twice (once for each model)
        assert mock_acreate.call_count == 2
        first_call = mock_acreate.call_args_list[0]
        second_call = mock_acreate.call_args_list[1]
        
        assert first_call[1]["model"] == "gpt-4o"
        assert second_call[1]["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_openai_error_handling():
    """Test error handling in OpenAIAnalyzer."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_FALLBACK_MODEL = "gpt-4"
        
        # Configure both models to fail
        mock_acreate.side_effect = openai.error.APIError("API Error")
        
        # Create analyzer and request
        analyzer = OpenAIAnalyzer()
        request = SentimentAnalysisRequest(text="Test text", extract_entities=False)
        
        # Call analyze_sentiment and expect exception
        with pytest.raises(openai.error.APIError):
            await analyzer.analyze_sentiment(request)


@pytest.mark.asyncio
async def test_openai_invalid_json_response():
    """Test handling of invalid JSON response from OpenAI."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Create invalid JSON response
        class MockInvalidResponse:
            class Choice:
                class Message:
                    content = "This is not valid JSON"
                
                def __init__(self):
                    self.message = self.Message()
            
            class Usage:
                def __init__(self):
                    self.total_tokens = 10
            
            def __init__(self):
                self.choices = [self.Choice()]
                self.model = "gpt-4o"
                self.usage = self.Usage()
        
        mock_acreate.return_value = MockInvalidResponse()
        
        # Create analyzer and request
        analyzer = OpenAIAnalyzer()
        request = SentimentAnalysisRequest(text="Test text", extract_entities=False)
        
        # Call analyze_sentiment and expect exception
        with pytest.raises(ValueError):
            await analyzer.analyze_sentiment(request)


# --- Fallback Functionality Tests ---

@pytest.mark.asyncio
async def test_analyze_text_sentiment_high_confidence(
    sample_text, mock_finbert_high_confidence
):
    """Test analyze_text_sentiment with high confidence from FinBERT."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Configure mock settings
        mock_settings.SENTIMENT_CONFIDENCE_THRESHOLD = 0.6
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "finbert"
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Configure mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_high_confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Create request
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_text_sentiment
        result = await analyze_text_sentiment(request)
        
        # Verify result
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.confidence == 0.92
        assert result.source == "finbert"
        
        # Verify OpenAI was not called
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_text_sentiment_low_confidence(
    sample_text, mock_finbert_low_confidence, mock_openai_response
):
    """Test analyze_text_sentiment with low confidence from FinBERT."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.SENTIMENT_CONFIDENCE_THRESHOLD = 0.6
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "finbert"
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Configure mock responses
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_low_confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_acreate.return_value = mock_openai_response
        
        # Create request
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_text_sentiment
        result = await analyze_text_sentiment(request)
        
        # Verify result comes from OpenAI
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.confidence == 0.89
        assert result.source == "openai"
        assert result.reasoning == "The text indicates strong financial performance with revenue growth."
        
        # Verify both APIs were called
        mock_post.assert_called_once()
        mock_acreate.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_text_sentiment_finbert_error(
    sample_text, mock_openai_response
):
    """Test analyze_text_sentiment when FinBERT fails."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.SENTIMENT_CONFIDENCE_THRESHOLD = 0.6
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "finbert"
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Configure FinBERT to fail
        mock_post.side_effect = httpx.RequestError("Connection error")
        
        # Configure OpenAI response
        mock_acreate.return_value = mock_openai_response
        
        # Create request
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_text_sentiment
        result = await analyze_text_sentiment(request)
        
        # Verify result comes from OpenAI
        assert result.sentiment == SentimentLabel.POSITIVE
        assert result.source == "openai"
        
        # Verify both APIs were called
        mock_post.assert_called_once()
        mock_acreate.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_text_sentiment_both_fail(sample_text):
    """Test analyze_text_sentiment when both FinBERT and OpenAI fail."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.SENTIMENT_CONFIDENCE_THRESHOLD = 0.6
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "finbert"
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Configure both to fail
        mock_post.side_effect = httpx.RequestError("Connection error")
        mock_acreate.side_effect = openai.error.APIError("API Error")
        
        # Create request
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_text_sentiment and expect exception
        with pytest.raises(openai.error.APIError):
            await analyze_text_sentiment(request)


@pytest.mark.asyncio
async def test_analyze_text_sentiment_custom_threshold(
    sample_text, mock_finbert_high_confidence, mock_openai_response
):
    """Test analyze_text_sentiment with custom threshold."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('httpx.AsyncClient.post') as mock_post, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.SENTIMENT_CONFIDENCE_THRESHOLD = 0.6  # Default threshold
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "finbert"
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Configure mock responses
        mock_response = MagicMock()
        mock_response.json.return_value = mock_finbert_high_confidence  # 0.92 confidence
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        mock_acreate.return_value = mock_openai_response
        
        # Create request
        request = SentimentAnalysisRequest(text=sample_text, extract_entities=False)
        
        # Call analyze_text_sentiment with custom threshold higher than FinBERT confidence
        result = await analyze_text_sentiment(request, confidence_threshold=0.95)
        
        # Verify result comes from OpenAI due to high threshold
        assert result.source == "openai"
        
        # Verify both APIs were called
        mock_post.assert_called_once()
        mock_acreate.assert_called_once()


# --- Entity Extraction Tests ---

@pytest.mark.asyncio
async def test_finbert_entity_extraction_symbols():
    """Test FinBERT entity extraction for stock symbols."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Create analyzer
        analyzer = FinBERTAnalyzer()
        
        # Test with multiple symbols
        text = "Investors are watching AAPL, MSFT, and GOOGL closely after the tech selloff."
        
        entities = await analyzer.extract_entities(text)
        
        # Find symbols
        symbols = [e for e in entities if e.type == EntityType.SYMBOL]
        symbol_texts = [e.text for e in symbols]
        
        assert "AAPL" in symbol_texts
        assert "MSFT" in symbol_texts
        assert "GOOGL" in symbol_texts


@pytest.mark.asyncio
async def test_finbert_entity_extraction_companies():
    """Test FinBERT entity extraction for company names."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Create analyzer
        analyzer = FinBERTAnalyzer()
        
        # Test with company names
        text = "Apple and Microsoft reported earnings that exceeded expectations, while Tesla struggled."
        
        entities = await analyzer.extract_entities(text)
        
        # Find companies
        companies = [e for e in entities if e.type == EntityType.COMPANY]
        company_texts = [e.text for e in companies]
        
        assert "Apple" in company_texts
        assert "Microsoft" in company_texts
        assert "Tesla" in company_texts


@pytest.mark.asyncio
async def test_finbert_entity_extraction_financial_instruments():
    """Test FinBERT entity extraction for financial instruments."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Configure mock settings
        mock_settings.FINBERT_API_KEY = "test_key"
        mock_settings.FINBERT_API_URL = "https://api.finbrain.tech/v1/sentiment"
        mock_settings.FINBERT_PROVIDER = "finbrain"
        
        # Create analyzer
        analyzer = FinBERTAnalyzer()
        
        # Test with financial instruments
        text = "Investors are moving money from stocks to bonds and treasury securities as recession fears grow."
        
        entities = await analyzer.extract_entities(text)
        
        # Find financial instruments
        instruments = [e for e in entities if e.type == EntityType.FINANCIAL_INSTRUMENT]
        instrument_texts = [e.text.lower() for e in instruments]
        
        assert "stocks" in instrument_texts
        assert "bonds" in instrument_texts
        assert "treasury" in instrument_texts


@pytest.mark.asyncio
async def test_openai_entity_extraction(sample_text, mock_openai_response):
    """Test OpenAI entity extraction."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings, \
         patch('openai.ChatCompletion.acreate') as mock_acreate:
        
        # Configure mock settings
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        # Configure mock response
        mock_acreate.return_value = mock_openai_response
        
        # Create analyzer
        analyzer = OpenAIAnalyzer()
        
        # Extract entities
        entities = await analyzer.extract_entities(sample_text)
        
        # Verify entities
        assert len(entities) == 2
        
        apple_entity = next((e for e in entities if e.text == "Apple"), None)
        aapl_entity = next((e for e in entities if e.text == "AAPL"), None)
        
        assert apple_entity is not None
        assert apple_entity.type == EntityType.COMPANY
        assert apple_entity.confidence == 0.95
        
        assert aapl_entity is not None
        assert aapl_entity.type == EntityType.SYMBOL
        assert aapl_entity.confidence == 0.98


@pytest.mark.asyncio
async def test_get_sentiment_analyzer_factory():
    """Test get_sentiment_analyzer factory function."""
    with patch('app.services.sentiment_analysis.settings') as mock_settings:
        # Configure mock settings
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "finbert"
        
        # Get default analyzer
        analyzer = await get_sentiment_analyzer()
        assert isinstance(analyzer, FinBERTAnalyzer)
        
        # Force OpenAI
        analyzer = await get_sentiment_analyzer(force_provider="openai")
        assert isinstance(analyzer, OpenAIAnalyzer)
        
        # Force FinBERT
        analyzer = await get_sentiment_analyzer(force_provider="finbert")
        assert isinstance(analyzer, FinBERTAnalyzer)
        
        # Change default provider
        mock_settings.SENTIMENT_ANALYZER_PROVIDER = "openai"
        analyzer = await get_sentiment_analyzer()
        assert isinstance(analyzer, OpenAIAnalyzer)
