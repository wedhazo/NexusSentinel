from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Optional, Dict, Any
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("llama3-sentiment")

# Initialize FastAPI app
app = FastAPI(title="NexusSentinel LLaMA 3 Nuanced Sentiment Service")

# Model configuration
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load tokenizer and model
try:
    logger.info(f"Loading LLaMA 3 model on {DEVICE}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    # Load model with 8-bit quantization to reduce memory usage
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        load_in_8bit=True,
        torch_dtype=torch.float16
    )
    logger.info("LLaMA 3 model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load LLaMA 3 model: {str(e)}")
    raise RuntimeError(f"Model initialization failed: {str(e)}")

class TextInput(BaseModel):
    text: str
    context: Optional[str] = None
    max_tokens: int = 20
    temperature: float = 0.1

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    explanation: Optional[str] = None
    processing_time: float
    model: str = "llama3-8b"

def create_prompt(text: str, context: Optional[str] = None) -> str:
    """
    Create a prompt for the LLaMA 3 model to analyze financial sentiment.
    
    Args:
        text: The financial text to analyze
        context: Optional additional context about the stock or market
        
    Returns:
        A formatted prompt for LLaMA 3
    """
    base_prompt = f"""<|begin_of_text|><|user|>
You are a financial sentiment analysis expert. Analyze the sentiment of the following financial text and determine if it's positive, neutral, or negative. Pay special attention to sarcasm, implicit meaning, and financial jargon.

"""

    if context:
        base_prompt += f"Context: {context}\n\n"
    
    base_prompt += f"""Text: "{text}"

Please respond with just one of these sentiment labels: positive, neutral, or negative.
<|end_of_text|>

<|assistant|>"""

    return base_prompt

@app.post("/llama-sentiment", response_model=SentimentResponse)
async def analyze_llama_sentiment(data: TextInput) -> Dict[str, Any]:
    """
    Analyze the sentiment of financial text using LLaMA 3 with nuanced understanding.
    
    This endpoint is designed to handle complex financial texts including sarcasm,
    implicit meaning, and financial jargon.
    """
    start_time = time.time()
    
    try:
        # Create prompt for the model
        prompt = create_prompt(data.text, data.context)
        
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
        
        # Generate response with the model
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=data.max_tokens,
                temperature=data.temperature,
                do_sample=True if data.temperature > 0 else False,
            )
        
        # Decode the response
        result = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract sentiment from the result (assuming the model outputs "positive", "neutral", or "negative")
        # Remove the prompt from the result to get just the model's response
        response_text = result.replace(prompt, "").strip().lower()
        
        # Extract the sentiment label
        if "positive" in response_text:
            sentiment = "positive"
        elif "negative" in response_text:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        processing_time = time.time() - start_time
        
        return {
            "text": data.text,
            "sentiment": sentiment,
            "explanation": response_text,
            "processing_time": round(processing_time, 3),
            "model": "llama3-8b"
        }
    
    except Exception as e:
        logger.error(f"Error during LLaMA 3 inference: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Model inference error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint to verify if the model is loaded and ready"""
    gpu_info = "Not available"
    
    if torch.cuda.is_available():
        gpu_info = {
            "name": torch.cuda.get_device_name(0),
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB"
        }
    
    return {
        "status": "healthy",
        "model": MODEL_ID,
        "device": DEVICE,
        "gpu_info": gpu_info,
        "quantization": "8-bit"
    }

@app.post("/analyze-financial-context")
async def analyze_financial_context(data: TextInput) -> Dict[str, Any]:
    """
    Advanced endpoint that analyzes financial text with deeper context understanding.
    
    This endpoint is specifically designed for complex financial statements,
    earnings reports, and tweets that may contain sarcasm or implicit meaning.
    """
    start_time = time.time()
    
    # Create a more detailed prompt for complex analysis
    detailed_prompt = f"""<|begin_of_text|><|user|>
You are a financial sentiment analysis expert. Analyze the following financial text in detail.
Consider sarcasm, implicit meaning, financial jargon, and market context.

Text: "{data.text}"

Provide:
1. Overall sentiment (positive, neutral, or negative)
2. Brief explanation (1-2 sentences)
<|end_of_text|>

<|assistant|>"""
    
    try:
        # Tokenize the prompt
        inputs = tokenizer(detailed_prompt, return_tensors="pt").to(DEVICE)
        
        # Generate response with the model
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=100,  # Allow longer response for explanation
                temperature=data.temperature,
                do_sample=True if data.temperature > 0 else False,
            )
        
        # Decode the response
        result = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract the model's response
        response_text = result.replace(detailed_prompt, "").strip()
        
        # Try to extract sentiment from the response
        sentiment = "neutral"  # Default
        if "positive" in response_text.lower():
            sentiment = "positive"
        elif "negative" in response_text.lower():
            sentiment = "negative"
        
        processing_time = time.time() - start_time
        
        return {
            "text": data.text,
            "sentiment": sentiment,
            "detailed_analysis": response_text,
            "processing_time": round(processing_time, 3),
            "model": "llama3-8b"
        }
    
    except Exception as e:
        logger.error(f"Error during detailed LLaMA 3 analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Model inference error: {str(e)}"
        )
