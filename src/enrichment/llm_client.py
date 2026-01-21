"""
Gemini LLM Client Wrapper

Wrapper for Google Gemini 2.5 Flash API with rate limiting, retries, and error handling.
"""
import os
import logging
import time
from typing import Optional, Dict, Any
from functools import wraps

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    raise ImportError(
        "langchain-google-genai is required. "
        "Install with: pip install langchain-google-genai"
    )

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator


class GeminiClient:
    """
    Wrapper for Google Gemini 2.5 Flash API.
    
    Handles authentication, rate limiting, retries, and error handling.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.5,
        max_retries: int = 3,
        rate_limit_delay: float = 0.1
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key (reads from GEMINI_API_KEY env var if None)
            model_name: Model name (reads from GEMINI_MODEL_NAME env var if None, defaults to "gemini-2.5-flash")
            temperature: Sampling temperature (0.0-1.0, default: 0.5)
            max_retries: Maximum retry attempts for API calls
            rate_limit_delay: Delay between API calls in seconds (rate limiting)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not provided. Set it as an environment variable or pass api_key parameter."
            )
        
        # Get model name from parameter, env var, or default
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        self.temperature = temperature
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize LangChain Gemini client
        self.client = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=temperature,
        )
        
        logger.info(f"Initialized GeminiClient with model: {self.model_name}")
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate text using Gemini API.
        
        Args:
            prompt: User prompt text
            system_instruction: Optional system instruction
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails after retries
        """
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Build messages
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            # Call API
            response = self.client.invoke(messages)
            
            # Extract text from response
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate JSON response using Gemini API.
        
        Args:
            prompt: User prompt text (should request JSON output)
            system_instruction: Optional system instruction
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If response is not valid JSON
            Exception: If API call fails
        """
        import json
        
        # Add JSON format instruction to prompt
        json_prompt = f"{prompt}\n\nPlease respond with valid JSON only, no additional text."
        
        response_text = self.generate(json_prompt, system_instruction)
        
        # Try to extract JSON from response (handle markdown code blocks)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove closing ```
        response_text = response_text.strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}...")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
