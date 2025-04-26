from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Any, Optional
import uuid # Import uuid for generating unique IDs
from uuid import UUID # Import UUID for type hinting

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
    Represents a rich response from the LLM service, including metadata.
    """
    response_id: UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for this specific request-response pair.")
    request: LLMRequest = Field(..., description="The original request object that led to this response.")
    response: str = Field(..., description="The generated response text from the LLM.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Timestamp of when the request processing started.")
    completed_at: Optional[datetime] = Field(None, description="Timestamp of when the response generation completed.")
    elapsed_time_ms: Optional[float] = Field(None, description="Total time taken for the LLM to generate the response, in milliseconds.")
    model_name: Optional[str] = Field(None, description="The name of the model that generated the response.")
    finish_reason: Optional[str] = Field(None, description="Reason why the generation finished (e.g., 'stop', 'length'). Provided by some LLM APIs.")

# Type alias for data chunks yielded during streaming
StreamingChunk = str 