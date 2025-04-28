import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# Base properties shared by other schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    is_active: bool | None = True
    is_superuser: bool = False

# Properties required for user creation (includes password)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePassword123")

# Properties received via API on update (all optional)
class UserUpdate(BaseModel):
    email: EmailStr | None = Field(None, example="user@example.com")
    username: str | None = Field(None, min_length=3, max_length=50, example="john_doe")
    password: str | None = Field(None, min_length=8, example="NewSecurePassword123")
    is_active: bool | None = None
    is_superuser: bool | None = None

# Properties stored in DB (hashed password)
class UserInDBBase(UserBase):
    id: uuid.UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True # Enable ORM mode
    }

# Final schema for data stored in DB
class UserInDB(UserInDBBase):
    pass

# Properties to return to client (excludes password)
class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True # Enable ORM mode
    } 