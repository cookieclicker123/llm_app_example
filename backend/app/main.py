from fastapi import FastAPI

# Import the router
from backend.app.api import chat_router

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