import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from backend.app.models.chat import LLMRequest, LLMResponse
from backend.app.services.chat_service import handle_chat_request, handle_chat_stream
from backend.app.utils.ollama_client import create_ollama_generate_func, create_ollama_stream_func
from backend.app.core.types import LLMFunction, LLMStreamingFunction
# Import settings dependency
from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# --- Dependency Provider Functions --- #
# These functions create and return instances of our LLM clients.
# They will be called by FastAPI for each request needing them.
# Configuration could be injected here later (e.g., from settings).

def get_ollama_generate(app_settings: Settings = Depends(get_settings)) -> LLMFunction:
    """Dependency provider for the non-streaming Ollama client function."""
    # Pass config explicitly from the injected settings instance
    return create_ollama_generate_func(
        base_url=app_settings.OLLAMA_BASE_URL,
        default_model=app_settings.OLLAMA_DEFAULT_MODEL,
        timeout=app_settings.OLLAMA_REQUEST_TIMEOUT
    )

def get_ollama_stream(app_settings: Settings = Depends(get_settings)) -> LLMStreamingFunction:
    """Dependency provider for the streaming Ollama client function."""
    # Pass config explicitly from the injected settings instance
    return create_ollama_stream_func(
        base_url=app_settings.OLLAMA_BASE_URL,
        default_model=app_settings.OLLAMA_DEFAULT_MODEL,
        timeout=app_settings.OLLAMA_REQUEST_TIMEOUT
    )

# --- API Router --- #

router = APIRouter()

@router.post("/", response_model=LLMResponse)
async def chat_endpoint(
    request: LLMRequest,
    # Inject the LLM function dependency
    ollama_generate_func: LLMFunction = Depends(get_ollama_generate),
    # Inject the settings dependency
    app_settings: Settings = Depends(get_settings)
):
    """
    Endpoint for non-streaming chat requests.
    Injects dependencies (LLM function, settings) and calls the service layer.
    """
    try:
        logger.info(f"Received non-streaming chat request: {request.prompt[:50]}...")
        # Service function now receives the injected dependencies
        response = await handle_chat_request(request, ollama_generate_func, app_settings)
        logger.info("Successfully processed non-streaming chat request.")
        return response
    except Exception as e:
        logger.exception("Error handling non-streaming chat request")
        # Re-raise as HTTPException for FastAPI to handle
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@router.post("/stream")
async def chat_stream_endpoint(
    request: LLMRequest,
    # Inject the dependency using Depends
    ollama_stream_func: LLMStreamingFunction = Depends(get_ollama_stream)
):
    """
    Endpoint for streaming chat requests.
    Receives a prompt and streams back the LLM response chunk by chunk.
    Dependencies (like the LLM function) are injected.
    """
    try:
        logger.info(f"Received streaming chat request: {request.prompt[:50]}...")
        # Service function now receives the injected dependency
        stream_generator = handle_chat_stream(request, ollama_stream_func)
        
        # Return the async generator wrapped in a StreamingResponse
        return StreamingResponse(stream_generator, media_type="text/plain")
        # Note: For more complex streaming (e.g., JSON chunks), adjust media_type
        # and how chunks are formatted/yielded in the service/client.
        
    except Exception as e:
        logger.exception("Error handling streaming chat request")
        # Cannot return StreamingResponse on error easily, raise HTTPException
        # Client needs to handle potential connection drop or error status.
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}") 