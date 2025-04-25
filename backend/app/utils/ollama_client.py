import httpx
import json
import logging
from typing import AsyncGenerator

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Default Configuration (Consider moving to core.config later)
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "deepseek-r1:14b" # Example default
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60

def create_ollama_generate_func(
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    default_model: str = DEFAULT_OLLAMA_MODEL,
    timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS
) -> LLMFunction:
    """
    Factory function that creates an Ollama client function for generating full responses.

    Args:
        base_url: The base URL of the Ollama API.
        default_model: The default Ollama model to use if not specified in the request.
        timeout: Request timeout in seconds.

    Returns:
        An async function conforming to the LLMFunction type alias.
    """
    api_endpoint = f"{base_url}/api/generate"

    async def _generate(request: LLMRequest) -> LLMResponse:
        """
        Nested function that performs the actual API call.
        Conforms to LLMFunction.
        """
        model_name = request.model_name or default_model
        payload = {
            "model": model_name,
            "prompt": request.prompt,
            "stream": False,
            "options": request.options or {},
            # "context": [] 
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Sending request to Ollama: {api_endpoint} with model {model_name}")
                response = await client.post(api_endpoint, json=payload)
                response.raise_for_status()
                ollama_data = response.json()
                logger.info("Received successful response from Ollama.")

                return LLMResponse(
                    response=ollama_data.get("response", ""),
                    model_name=ollama_data.get("model", model_name),
                )

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
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    default_model: str = DEFAULT_OLLAMA_MODEL,
    timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS
) -> LLMStreamingFunction:
    """
    Factory function that creates an Ollama client function for streaming responses.

    Args:
        base_url: The base URL of the Ollama API.
        default_model: The default Ollama model to use if not specified in the request.
        timeout: Request timeout in seconds.

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
            # "context": []
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
                                # break # Optional: stop on error

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

# Example of creating and typing the functions (optional, for clarity)
# ollama_generate: LLMFunction = create_ollama_generate_func()
# ollama_stream: LLMStreamingFunction = create_ollama_stream_func() 