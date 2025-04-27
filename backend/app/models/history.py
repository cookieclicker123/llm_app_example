from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    """Represents a single message in the chat history."""
    role: str  # Typically "user" or "assistant"
    content: str

class ConversationHistory(BaseModel):
    """Represents the entire conversation history for a session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[ChatMessage] = Field(default_factory=list)

    model_config = {
        "json_encoders": {
            datetime: lambda dt: dt.isoformat(),
        },
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "abc-123",
                    "created_at": "2023-10-27T10:00:00Z",
                    "messages": [
                        {"role": "user", "content": "Hello there!"},
                        {"role": "assistant", "content": "Hi! How can I help?"},
                        {"role": "user", "content": "Tell me about FastAPI."},
                    ]
                }
            ]
        }
    }

class HistoryEntry(BaseModel):
    """Represents a single turn in the conversation history."""
    entry_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: str
    user_message: str
    llm_response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow) # Use utcnow for consistency 