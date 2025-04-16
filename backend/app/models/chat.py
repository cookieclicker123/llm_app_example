from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Any, Optional

class LLMRequest(BaseModel):
    """
    Represents a request to the LLM service.
    """
    prompt: str = Field(..., description="The user's input prompt for the LLM.")
    session_id: Optional[str] = Field(None, description="An optional session identifier for maintaining conversation context.")
    model_name: Optional[str] = Field(None, description="Optional specific model name to use (if supported by the backend).")
    options: Optional[dict[str, Any]] = Field(None, description="Optional dictionary for passing specific LLM parameters like temperature, max_tokens, etc.")


class LLMResponse(BaseModel):
    """
    Represents a response from the LLM service.
    """
    response: str = Field(..., description="The generated response text from the LLM.")
    request_id: Optional[str] = Field(None, description="An optional identifier linking this response to the original request.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Timestamp of when the response was generated.")
    model_name: Optional[str] = Field(None, description="The name of the model that generated the response.")
    finish_reason: Optional[str] = Field(None, description="Reason why the generation finished (e.g., 'stop', 'length'). Provided by some LLM APIs.")

# Type alias for data chunks yielded during streaming
StreamingChunk = str 