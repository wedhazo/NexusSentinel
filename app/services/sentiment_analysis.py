"""
Sentiment Analysis Service for NexusSentinel.

This module provides sentiment analysis capabilities using multiple providers:
- FinBERT/FinGPT API for financial sentiment analysis
- OpenAI GPT models as a fallback for more nuanced analysis

The service supports entity extraction to identify companies, stock symbols,
and financial instruments mentioned in the text.
"""

import abc
import re
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set, Union, ClassVar
import httpx
from pydantic import BaseModel, Field, HttpUrl, validator
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time  # Added explicit import for time module

from app.config import settings

# Configure logger
logger = logging.getLogger(__name__)


# --- Pydantic Models ---

class SentimentLabel(str, Enum):
    """Enumeration of possible sentiment labels."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Enumeration of possible entity types."""
    COMPANY = "company"
    SYMBOL = "symbol"
    FINANCIAL_INSTRUMENT = "financial_instrument"
    OTHER = "other"


class Entity(BaseModel):
    """Model representing an extracted entity."""
    text: str = Field(..., description="The extracted entity text")
    type: EntityType = Field(..., description="Type of the entity")
    confidence: float = Field(..., description="Confidence score for the entity extraction", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the entity")


class SentimentAnalysisRequest(BaseModel):
    """Model for sentiment analysis request."""
    text: str = Field(..., description="Text to analyze for sentiment")
    source: Optional[str] = Field(None, description="Source of the text (e.g., 'news', 'twitter', 'reddit')")
    extract_entities: bool = Field(True, description="Whether to extract entities from the text")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the request")


class SentimentAnalysisResponse(BaseModel):
    """Model for sentiment analysis response."""
    text: str = Field(..., description="Original text that was analyzed")
    sentiment: SentimentLabel = Field(..., description="Detected sentiment label")
    confidence: float = Field(..., description="Confidence score for the sentiment", ge=0.0, le=1.0)
    source: str = Field(..., description="Source of the analysis (e.g., 'finbert', 'openai')")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the sentiment classification")
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities from the text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the analysis")

    class Config:
        schema_extra = {
            "example": {
                "text": "Apple's new product line exceeds analyst expectations, driving stock up 5%.",
                "sentiment": "positive",
                "confidence": 0.92,
                "source": "finbert",
                "reasoning": "The text indicates a positive financial outcome with stock price increase and exceeding expectations.",
                "entities": [
                    {
                        "text": "Apple",
                        "type": "company",
                        "confidence": 0.98,
                        "metadata": {"possible_symbols": ["AAPL"]}
                    }
                ],
                "metadata": {
                    "processing_time_ms": 156
                }
            }
        }


# --- Analyzer Interface ---

class SentimentAnalyzer(abc.ABC):
    """Abstract base class for sentiment analyzers."""

    @abc.abstractmethod
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
        """
        Analyze the sentiment of the provided text.
        
        Args:
            request: The sentiment analysis request containing text and options
            
        Returns:
            SentimentAnalysisResponse with sentiment label, confidence, and optional entities
        """
        pass
    
    @abc.abstractmethod
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from the provided text.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            List of extracted entities
        """
        pass


# --- FinBERT Analyzer ---

class FinBERTProvider(str, Enum):
    """Supported FinBERT API providers."""
    FINBRAIN = "finbrain"
    FINGPT = "fingpt"
    CUSTOM = "custom"


class FinBERTAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using FinBERT/FinGPT API."""
    
    # Common stock symbols regex pattern (1-5 uppercase letters, optionally followed by a dot and more letters)
    STOCK_SYMBOL_PATTERN: ClassVar[re.Pattern] = re.compile(r'\b[A-Z]{1,5}(?:\.[A-Z]+)?\b')
    
    # Common financial instruments keywords
    FINANCIAL_INSTRUMENTS: ClassVar[Set[str]] = {
        "bond", "bonds", "etf", "etfs", "future", "futures", "option", "options",
        "stock", "stocks", "share", "shares", "index", "indices", "fund", "funds",
        "treasury", "treasuries", "forex", "currency", "currencies", "crypto",
        "cryptocurrency", "cryptocurrencies", "commodity", "commodities"
    }
    
    def __init__(self):
        """Initialize the FinBERT analyzer with configuration from settings."""
        self.api_key = settings.FINBERT_API_KEY
        self.api_url = settings.FINBERT_API_URL
        self.provider = FinBERTProvider(settings.FINBERT_PROVIDER.lower())
        self.timeout = settings.FINBERT_TIMEOUT_SECONDS
        self.auth_header = self._get_auth_header()
        
        # Validate configuration
        if not self.api_key:
            logger.warning("FinBERT API key not configured")
        if not self.api_url:
            logger.warning("FinBERT API URL not configured")
            
        logger.info(f"Initialized FinBERT analyzer with provider: {self.provider}")
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get the appropriate authentication header based on the provider."""
        if self.provider == FinBERTProvider.FINBRAIN:
            return {"X-API-KEY": self.api_key}
        elif self.provider == FinBERTProvider.FINGPT:
            return {"Authorization": f"Bearer {self.api_key}"}
        else:  # CUSTOM
            auth_method = settings.FINBERT_AUTH_METHOD.lower()
            if auth_method == "bearer":
                return {"Authorization": f"Bearer {self.api_key}"}
            elif auth_method == "api-key" or auth_method == "apikey":
                return {"X-API-KEY": self.api_key}
            else:
                return {settings.FINBERT_AUTH_HEADER: self.api_key}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
        """
        Analyze sentiment using the FinBERT API.
        
        Args:
            request: The sentiment analysis request
            
        Returns:
            SentimentAnalysisResponse with results from FinBERT
            
        Raises:
            httpx.RequestError: If there's a network error
            httpx.HTTPStatusError: If the API returns an error status
            ValueError: If the API response is invalid
        """
        try:
            # Prepare request payload based on provider
            if self.provider == FinBERTProvider.FINBRAIN:
                payload = {"text": request.text}
            elif self.provider == FinBERTProvider.FINGPT:
                payload = {"text": request.text, "model": "sentiment"}
            else:  # CUSTOM
                payload = {
                    "text": request.text,
                    **(request.metadata or {})
                }
            
            start_time = time.time()
            
            # Make API request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=self.auth_header
                )
                response.raise_for_status()
                
                # Parse response based on provider
                data = response.json()
                
                if self.provider == FinBERTProvider.FINBRAIN:
                    sentiment_label = data.get("sentiment", "").lower()
                    confidence = data.get("confidence", 0.0)
                elif self.provider == FinBERTProvider.FINGPT:
                    sentiment_label = data.get("label", "").lower()
                    confidence = data.get("score", 0.0)
                else:  # CUSTOM
                    sentiment_mapping = {
                        settings.FINBERT_POSITIVE_LABEL.lower(): SentimentLabel.POSITIVE,
                        settings.FINBERT_NEUTRAL_LABEL.lower(): SentimentLabel.NEUTRAL,
                        settings.FINBERT_NEGATIVE_LABEL.lower(): SentimentLabel.NEGATIVE
                    }
                    
                    raw_label = data.get(settings.FINBERT_LABEL_FIELD, "").lower()
                    sentiment_label = sentiment_mapping.get(raw_label, SentimentLabel.UNKNOWN)
                    confidence = float(data.get(settings.FINBERT_CONFIDENCE_FIELD, 0.0))
                
                # Map to standard sentiment labels
                if "positive" in sentiment_label:
                    sentiment = SentimentLabel.POSITIVE
                elif "negative" in sentiment_label:
                    sentiment = SentimentLabel.NEGATIVE
                elif "neutral" in sentiment_label:
                    sentiment = SentimentLabel.NEUTRAL
                else:
                    sentiment = SentimentLabel.UNKNOWN
                
                # Extract entities if requested
                entities = []
                if request.extract_entities:
                    entities = await self.extract_entities(request.text)
                
                processing_time = int((time.time() - start_time) * 1000)  # in milliseconds
                
                return SentimentAnalysisResponse(
                    text=request.text,
                    sentiment=sentiment,
                    confidence=confidence,
                    source="finbert",
                    entities=entities,
                    metadata={
                        "processing_time_ms": processing_time,
                        "provider": self.provider,
                        "raw_response": data
                    }
                )
                
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"FinBERT API error: {str(e)}")
            raise
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing FinBERT response: {str(e)}")
            raise ValueError(f"Invalid response from FinBERT API: {str(e)}")
    
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract financial entities from text using regex patterns.
        
        This is a simple implementation using regex patterns. For production use,
        consider using a more sophisticated NER model.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract potential stock symbols
        symbols = self.STOCK_SYMBOL_PATTERN.findall(text)
        for symbol in symbols:
            # Exclude common English words that might match the pattern
            if symbol not in {"A", "I", "ME", "MY", "IT", "IF", "IS", "BE", "TO", "OF", "IN", "FOR"}:
                entities.append(Entity(
                    text=symbol,
                    type=EntityType.SYMBOL,
                    confidence=0.8,  # Simple regex match, moderate confidence
                    metadata={}
                ))
        
        # Extract financial instruments using keyword matching
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            if word in self.FINANCIAL_INSTRUMENTS:
                entities.append(Entity(
                    text=word,
                    type=EntityType.FINANCIAL_INSTRUMENT,
                    confidence=0.7,  # Simple keyword match, moderate confidence
                    metadata={}
                ))
        
        # Extract potential company names (simple heuristic for capitalized phrases)
        # This is a very basic approach and will have many false positives
        company_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b')
        potential_companies = company_pattern.findall(text)
        for company in potential_companies:
            # Exclude short names and common English words
            if len(company) > 3 and company not in {"I", "Me", "You", "He", "She", "They", "We", "It"}:
                entities.append(Entity(
                    text=company,
                    type=EntityType.COMPANY,
                    confidence=0.6,  # Simple heuristic, lower confidence
                    metadata={}
                ))
        
        return entities


# --- OpenAI Analyzer ---

class OpenAIAnalyzer(SentimentAnalyzer):
    """Sentiment analyzer using OpenAI GPT models."""
    
    # System prompt for financial sentiment analysis
    SYSTEM_PROMPT = """
    You are a financial sentiment analysis expert. Analyze the given text and determine if it has a positive, neutral, or negative sentiment from a financial perspective.
    
    Focus on financial implications, market reactions, and economic indicators. Consider how the information would likely impact stock prices, investor sentiment, or market conditions.
    
    Provide your analysis in JSON format with the following fields:
    - sentiment: "positive", "neutral", or "negative"
    - confidence: a number between 0 and 1 indicating your confidence in the assessment
    - reasoning: a brief explanation of your reasoning
    - entities: a list of financial entities mentioned (companies, symbols, financial instruments)
    
    For entity extraction, include:
    - text: the entity text
    - type: "company", "symbol", or "financial_instrument"
    - confidence: a number between 0 and 1
    
    Respond with JSON only.
    """
    
    def __init__(self):
        """Initialize the OpenAI analyzer with configuration from settings."""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.fallback_model = settings.OPENAI_FALLBACK_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        
        logger.info(f"Initialized OpenAI analyzer with model: {self.model} (fallback: {self.fallback_model})")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.error.APIError, openai.error.ServiceUnavailableError)),
        reraise=True
    )
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
        """
        Analyze sentiment using OpenAI GPT models.
        
        Args:
            request: The sentiment analysis request
            
        Returns:
            SentimentAnalysisResponse with results from OpenAI
            
        Raises:
            openai.error.OpenAIError: If there's an error with the OpenAI API
            ValueError: If the API response is invalid
        """
        try:
            start_time = time.time()
            
            # Prepare messages for the API
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": request.text}
            ]
            
            # Try primary model first
            try:
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
            except (openai.error.InvalidRequestError, openai.error.APIError) as e:
                logger.warning(f"Error with primary model {self.model}, falling back to {self.fallback_model}: {str(e)}")
                # Fallback to secondary model
                response = await openai.ChatCompletion.acreate(
                    model=self.fallback_model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
            
            # Parse the response
            response_text = response.choices[0].message.content
            
            try:
                import json
                data = json.loads(response_text)
                
                # Extract sentiment and confidence
                sentiment_label = data.get("sentiment", "").lower()
                confidence = float(data.get("confidence", 0.9))  # Default high confidence for GPT
                reasoning = data.get("reasoning", "")
                
                # Map to standard sentiment labels
                if "positive" in sentiment_label:
                    sentiment = SentimentLabel.POSITIVE
                elif "negative" in sentiment_label:
                    sentiment = SentimentLabel.NEGATIVE
                elif "neutral" in sentiment_label:
                    sentiment = SentimentLabel.NEUTRAL
                else:
                    sentiment = SentimentLabel.UNKNOWN
                
                # Extract entities
                raw_entities = data.get("entities", [])
                entities = []
                
                if request.extract_entities and raw_entities:
                    for entity_data in raw_entities:
                        entity_type = entity_data.get("type", "").lower()
                        if "company" in entity_type:
                            entity_type = EntityType.COMPANY
                        elif "symbol" in entity_type:
                            entity_type = EntityType.SYMBOL
                        elif "financial" in entity_type or "instrument" in entity_type:
                            entity_type = EntityType.FINANCIAL_INSTRUMENT
                        else:
                            entity_type = EntityType.OTHER
                        
                        entities.append(Entity(
                            text=entity_data.get("text", ""),
                            type=entity_type,
                            confidence=float(entity_data.get("confidence", 0.8)),
                            metadata={}
                        ))
                
                processing_time = int((time.time() - start_time) * 1000)  # in milliseconds
                
                return SentimentAnalysisResponse(
                    text=request.text,
                    sentiment=sentiment,
                    confidence=confidence,
                    source="openai",
                    reasoning=reasoning,
                    entities=entities,
                    metadata={
                        "processing_time_ms": processing_time,
                        "model": response.model,
                        "tokens_used": response.usage.total_tokens
                    }
                )
                
            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                logger.error(f"Error parsing OpenAI response: {str(e)}, response: {response_text}")
                raise ValueError(f"Invalid response from OpenAI API: {str(e)}")
                
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities using OpenAI's capabilities.
        
        This is implemented as part of the analyze_sentiment method for efficiency.
        This separate method is provided for interface compatibility.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            List of extracted entities
        """
        # Create a minimal request just for entity extraction
        request = SentimentAnalysisRequest(text=text, extract_entities=True)
        response = await self.analyze_sentiment(request)
        return response.entities


# --- Factory Function ---

async def get_sentiment_analyzer(force_provider: Optional[str] = None) -> SentimentAnalyzer:
    """
    Get the appropriate sentiment analyzer based on configuration or forced provider.
    
    Args:
        force_provider: Optional provider to force ("finbert" or "openai")
        
    Returns:
        An instance of a SentimentAnalyzer implementation
    """
    if force_provider == "openai":
        return OpenAIAnalyzer()
    elif force_provider == "finbert":
        return FinBERTAnalyzer()
    
    # Default behavior based on configuration
    if settings.SENTIMENT_ANALYZER_PROVIDER.lower() == "openai":
        return OpenAIAnalyzer()
    else:
        return FinBERTAnalyzer()


# --- Combined Analysis Function ---

async def analyze_text_sentiment(
    request: SentimentAnalysisRequest,
    confidence_threshold: float = None
) -> SentimentAnalysisResponse:
    """
    Analyze text sentiment with fallback mechanism.
    
    This function first tries the FinBERT analyzer. If the confidence is below
    the threshold, it falls back to OpenAI for a more nuanced analysis.
    
    Args:
        request: The sentiment analysis request
        confidence_threshold: Optional override for confidence threshold
        
    Returns:
        SentimentAnalysisResponse from either FinBERT or OpenAI
    """
    # Use configured threshold if not explicitly provided
    if confidence_threshold is None:
        confidence_threshold = settings.SENTIMENT_CONFIDENCE_THRESHOLD
    
    # First try FinBERT
    try:
        finbert_analyzer = await get_sentiment_analyzer(force_provider="finbert")
        finbert_result = await finbert_analyzer.analyze_sentiment(request)
        
        # If confidence is high enough, return the result
        if finbert_result.confidence >= confidence_threshold:
            logger.info(f"Using FinBERT result with confidence {finbert_result.confidence}")
            return finbert_result
        
        logger.info(f"FinBERT confidence {finbert_result.confidence} below threshold {confidence_threshold}, falling back to OpenAI")
    except Exception as e:
        logger.error(f"FinBERT analysis failed, falling back to OpenAI: {str(e)}")
    
    # Fallback to OpenAI
    try:
        openai_analyzer = await get_sentiment_analyzer(force_provider="openai")
        openai_result = await openai_analyzer.analyze_sentiment(request)
        logger.info(f"Using OpenAI result with confidence {openai_result.confidence}")
        return openai_result
    except Exception as e:
        logger.error(f"OpenAI analysis failed: {str(e)}")
        # If we have a FinBERT result, return it even if confidence was low
        if 'finbert_result' in locals():
            logger.warning(f"Falling back to low-confidence FinBERT result after OpenAI failure")
            return finbert_result
        # Otherwise, re-raise the exception
        raise
