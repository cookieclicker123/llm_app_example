from fastapi import FastAPI, Request, HTTPException
import logging # Import logging
import sys # Import sys to output to stdout
from contextlib import asynccontextmanager
import httpx
import redis.asyncio as redis # Import async redis client
from backend.app.core.config import settings # Assuming settings are needed

# Import the router
from backend.app.api import chat_router

# --- Logging Configuration --- #
# Configure logging to output INFO level messages to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout, # Ensure logs go to stdout for Docker
)
# Set logger for the specific module if needed, but basicConfig for root should suffice
# logging.getLogger("backend.app.services.chat_service").setLevel(logging.DEBUG)
# ---------------------------- #

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    logger.info("Application startup: Connecting to Redis...")
    try:
        app.state.redis_pool = redis.ConnectionPool.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            decode_responses=True # Decode responses to UTF-8
        )
        # Test connection
        async with redis.Redis(connection_pool=app.state.redis_pool) as conn:
            await conn.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # Optionally, raise the exception or handle startup failure
        app.state.redis_pool = None # Ensure pool is None if connection failed

    logger.info("Application startup: Warming up default Ollama model...")
    warmup_payload = {
        "model": settings.OLLAMA_DEFAULT_MODEL,
        "prompt": "Warmup prompt (content doesn't matter much)", # Simple prompt
        "stream": False,
        "keep_alive": "10m" # Keep it warm for 10 mins after warmup
    }
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_REQUEST_TIMEOUT * 2) as client: # Longer timeout for warmup
            # Use the URL from settings
            api_endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"
            response = await client.post(api_endpoint, json=warmup_payload)
            response.raise_for_status() # Check if warmup call was successful
            logger.info(f"Ollama model '{settings.OLLAMA_DEFAULT_MODEL}' warmup successful.")
    except Exception as e:
        logger.error(f"Ollama model warmup failed: {e}")

    yield
    # Code to run on shutdown (if any)
    if hasattr(app.state, 'redis_pool') and app.state.redis_pool:
        logger.info("Application shutdown: Closing Redis connection pool...")
        # redis-py >= 5.0 uses close() and await_closed() instead of disconnect()
        await app.state.redis_pool.disconnect() # Close connections gracefully
        logger.info("Redis connection pool closed.")

    logger.info("Application shutdown.")

app = FastAPI(
    title="End-to-End LLM App",
    description="An application demonstrating best practices for building LLM apps.",
    version="0.1.0",
    lifespan=lifespan # Add the lifespan manager
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the LLM App API!"}

# Include the chat router
app.include_router(
    chat_router,
    prefix="/api/v1/chat", # Route prefix for chat endpoints
    tags=["Chat"]         # Tag for OpenAPI documentation
)

# Add other routers here as the application grows 