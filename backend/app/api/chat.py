import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import redis.asyncio as redis # Import redis
# Add DB Session and User model imports
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User

from backend.app.models.chat import LLMRequest, LLMResponse
from backend.app.services.chat_service import handle_chat_request, handle_chat_stream
from backend.app.utils.ollama_client import create_ollama_generate_func, create_ollama_stream_func
from backend.app.core.types import LLMFunction, LLMStreamingFunction
# Import settings dependency
from backend.app.core.config import Settings, get_settings
# Import dependency providers
from backend.app.core.dependencies import get_redis
from backend.app.db.session import get_db_session # Import DB session dependency
from backend.app.core.security import get_current_active_user # Import auth dependency

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
    # Inject other dependencies
    app_settings: Settings = Depends(get_settings),
    redis_conn: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db_session), # Inject DB session
    current_user: User = Depends(get_current_active_user) # Inject current user
):
    """
    Endpoint for non-streaming chat requests.
    Injects dependencies (LLM function, settings, Redis, DB session, current user) and calls the service layer.
    """
    try:
        logger.info(f"Received non-streaming chat request from user {current_user.username}: {request.prompt[:50]}...")
        # Service function now receives the injected dependencies
        response = await handle_chat_request(
            request,
            ollama_generate_func,
            app_settings,
            redis_conn=redis_conn,
            db=db,              # Pass db session
            current_user=current_user # Pass current user
        )
        logger.info("Successfully processed non-streaming chat request.")
        return response
    # Catch specific HTTPExceptions from services (like 403/404)
    except HTTPException as http_exc:
        logger.warning(f"HTTP Exception during non-streaming chat: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception("Error handling non-streaming chat request")
        # Re-raise as HTTPException for FastAPI to handle
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {type(e).__name__}")

@router.post("/stream")
async def chat_stream_endpoint(
    request: LLMRequest,
    # Inject the dependency using Depends
    ollama_stream_func: LLMStreamingFunction = Depends(get_ollama_stream),
    redis_conn: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db_session), # Inject DB session
    current_user: User = Depends(get_current_active_user) # Inject current user
):
    """
    Endpoint for streaming chat requests.
    Receives a prompt and streams back the LLM response chunk by chunk.
    Dependencies (LLM function, Redis, DB session, current user) are injected.
    """
    try:
        logger.info(f"Received streaming chat request from user {current_user.username}: {request.prompt[:50]}...")
        # Service function now receives the injected dependencies
        stream_generator = handle_chat_stream(
            request,
            ollama_stream_func,
            redis_conn=redis_conn,
            db=db,              # Pass db session
            current_user=current_user # Pass current user
        )
        
        # Return the async generator wrapped in a StreamingResponse
        # Define headers to prevent buffering in intermediate proxies/servers
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Specific header for Nginx
        }
        return StreamingResponse(stream_generator, media_type="text/event-stream", headers=headers)
        
    # Catch specific HTTPExceptions from services (like 403/404)
    except HTTPException as http_exc:
        logger.warning(f"HTTP Exception during streaming chat: {http_exc.status_code} - {http_exc.detail}")
        # Cannot return StreamingResponse on error easily, raise HTTPException
        # Client needs to handle potential connection drop or error status.
        raise http_exc
    except Exception as e:
        logger.exception("Error handling streaming chat request")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {type(e).__name__}") 