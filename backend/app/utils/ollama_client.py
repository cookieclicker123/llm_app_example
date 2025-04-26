import httpx
import json
import logging
from typing import AsyncGenerator, Dict, Any

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
# Import the settings instance
from backend.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
# Logging level can be configured via settings.LOG_LEVEL elsewhere
# logging.basicConfig(level=settings.LOG_LEVEL)

# Default Configuration is now read from settings
# DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
# DEFAULT_OLLAMA_MODEL = "deepseek-r1:14b"
# DEFAULT_REQUEST_TIMEOUT_SECONDS = 60

def create_ollama_generate_func(
    # Default values are now taken from the settings object
    base_url: str = settings.OLLAMA_BASE_URL,
    default_model: str = settings.OLLAMA_DEFAULT_MODEL,
    timeout: int = settings.OLLAMA_REQUEST_TIMEOUT
) -> LLMFunction:
    """
    Factory function that creates an Ollama client function for generating full responses.
    Returns a dictionary containing the core response data.

    Configuration is sourced from the application settings.

    Returns:
        An async function conforming to the LLMFunction type alias.
    """
    api_endpoint = f"{base_url}/api/generate"

    async def _generate(request: LLMRequest) -> Dict[str, Any]:
        """
        Nested function that performs the actual API call.
        Returns a dictionary.
        """
        model_name = request.model_name or default_model
        payload = {
            "model": model_name,
            "prompt": request.prompt,
            "stream": False,
            "options": request.options or {},
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Sending request to Ollama: {api_endpoint} with model {model_name}")
                response = await client.post(api_endpoint, json=payload)
                response.raise_for_status()
                ollama_data = response.json()
                logger.info("Received successful response from Ollama.")

                return {
                    "response": ollama_data.get("response", ""),
                    "model_name": ollama_data.get("model", model_name),
                    "finish_reason": ollama_data.get("done_reason"),
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Connection error to Ollama at {api_endpoint}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from Ollama: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred interacting with Ollama: {e}")
            raise

    return _generate # Return the nested function

def create_ollama_stream_func(
    # Default values are now taken from the settings object
    base_url: str = settings.OLLAMA_BASE_URL,
    default_model: str = settings.OLLAMA_DEFAULT_MODEL,
    timeout: int = settings.OLLAMA_REQUEST_TIMEOUT
) -> LLMStreamingFunction:
    """
    Factory function that creates an Ollama client function for streaming responses.

    Configuration is sourced from the application settings.

    Returns:
        An async function conforming to the LLMStreamingFunction type alias.
    """
    api_endpoint = f"{base_url}/api/generate"

    async def _stream(request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        Nested function that performs the actual streaming API call.
        Conforms to LLMStreamingFunction.
        """
        model_name = request.model_name or default_model
        payload = {
            "model": model_name,
            "prompt": request.prompt,
            "stream": True,
            "options": request.options or {},
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Streaming request to Ollama: {api_endpoint} with model {model_name}")
                async with client.stream("POST", api_endpoint, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk_data = json.loads(line)
                                text_chunk = chunk_data.get("response", "")
                                if text_chunk:
                                    yield text_chunk
                                if chunk_data.get("done"):
                                    logger.info("Ollama stream finished.")
                                    break
                            except json.JSONDecodeError:
                                logger.warning(f"Received non-JSON line from Ollama stream: {line}")
                            except Exception as e:
                                logger.exception(f"Error processing Ollama stream chunk: {e}")

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error on stream start: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Connection error to Ollama at {api_endpoint}: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred starting Ollama stream: {e}")
            raise

    return _stream # Return the nested function