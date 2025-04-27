import httpx
import json
import logging
from typing import AsyncGenerator, Dict, Any, List

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
# Import the settings instance
from backend.app.core.config import settings
# Import HistoryEntry for type hinting
from backend.app.models.history import HistoryEntry

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
    Factory function that creates an Ollama client function for non-streaming chat.
    Uses the /api/chat endpoint and handles conversation history.
    Returns a dictionary containing the core response data.

    Configuration is sourced from the application settings.

    Returns:
        An async function conforming to the LLMFunction type alias.
    """
    api_endpoint = f"{base_url}/api/chat"

    async def _generate(request: LLMRequest, history: List[HistoryEntry] = None) -> Dict[str, Any]:
        """
        Nested function that performs the actual non-streaming chat API call.
        Accepts optional conversation history.
        Returns a dictionary.
        """
        model_name = request.model_name or default_model

        # Construct the messages payload from history and current prompt
        messages = []
        if history:
            for entry in history:
                messages.append({"role": "user", "content": entry.user_message})
                messages.append({"role": "assistant", "content": entry.llm_response})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": request.options or {},
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Sending request to Ollama Chat API: {api_endpoint} with model {model_name}")
                response = await client.post(api_endpoint, json=payload)
                response.raise_for_status()
                ollama_data = response.json()

                # Extract data from the /api/chat response structure
                message_content = ollama_data.get("message", {}).get("content", "")
                # Use done_reason if available, otherwise map 'done: true' to 'stop'
                done_reason = ollama_data.get("done_reason")
                if done_reason is None and ollama_data.get("done") is True:
                    done_reason = "stop"

                logger.info("Received successful response from Ollama Chat API.")

                return {
                    "response": message_content,
                    "model_name": ollama_data.get("model", model_name),
                    "finish_reason": done_reason,
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
    Factory function that creates an Ollama client function for streaming chat responses.
    Uses the /api/chat endpoint and handles conversation history.

    Configuration is sourced from the application settings.

    Returns:
        An async function conforming to the LLMStreamingFunction type alias.
    """
    api_endpoint = f"{base_url}/api/chat"

    async def _stream(request: LLMRequest, history: List[HistoryEntry] = None) -> AsyncGenerator[StreamingChunk, None]:
        """
        Nested function that performs the actual streaming chat API call.
        Accepts optional conversation history.
        Yields response chunks.
        """
        model_name = request.model_name or default_model

        # Construct the messages payload from history and current prompt
        messages = []
        if history:
            for entry in history:
                messages.append({"role": "user", "content": entry.user_message})
                messages.append({"role": "assistant", "content": entry.llm_response})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "options": request.options or {},
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Streaming request to Ollama Chat API: {api_endpoint} with model {model_name}")
                async with client.stream("POST", api_endpoint, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk_data = json.loads(line)
                                # Parse content from the /api/chat streaming format
                                message_chunk = chunk_data.get("message", {})
                                text_chunk = message_chunk.get("content", "")
                                if text_chunk:
                                    yield text_chunk
                                # Check the 'done' flag in the main chunk object
                                if chunk_data.get("done") is True:
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