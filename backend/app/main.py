from fastapi import FastAPI

app = FastAPI(
    title="End-to-End LLM App",
    description="An application demonstrating best practices for building LLM apps.",
    version="0.1.0",
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the LLM App API!"}

# Placeholder for including API routers
# from .api import chat_router # Example
# app.include_router(chat_router, prefix="/chat", tags=["Chat"])

# Add other routers here 