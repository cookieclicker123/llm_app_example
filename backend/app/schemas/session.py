import uuid
from datetime import datetime
from pydantic import BaseModel, Field

# Base properties for a session
class SessionBase(BaseModel):
    session_uuid: uuid.UUID = Field(..., example=uuid.uuid4())
    title: str | None = Field(None, max_length=255, example="My first chat session")

# Properties for creating a session (implicitly linked to current user)
class SessionCreate(SessionBase):
    pass

# Properties for updating a session (only title is updatable here)
class SessionUpdate(BaseModel):
    title: str | None = Field(None, max_length=255, example="Updated chat session title")

# Properties stored in DB
class SessionInDBBase(SessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    last_accessed_at: datetime

    model_config = {
        "from_attributes": True # Enable ORM mode
    }

# Final schema for data stored in DB
class SessionInDB(SessionInDBBase):
    pass

# Properties to return to client
class SessionRead(SessionBase):
    id: uuid.UUID # Use the internal DB ID, or session_uuid if preferred for API
    user_id: uuid.UUID
    created_at: datetime
    last_accessed_at: datetime

    model_config = {
        "from_attributes": True # Enable ORM mode
    } 