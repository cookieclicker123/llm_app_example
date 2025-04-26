from fastapi import FastAPI
import logging # Import logging
import sys # Import sys to output to stdout

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

app = FastAPI(
    title="End-to-End LLM App",
    description="An application demonstrating best practices for building LLM apps.",
    version="0.1.0",
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