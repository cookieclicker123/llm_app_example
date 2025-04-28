from pydantic import BaseModel

# Schema for the data encoded within the JWT token
class TokenData(BaseModel):
    username: str | None = None
    # Add other fields like user ID, roles, etc., if needed later

# Schema for the response when requesting a token
class Token(BaseModel):
    access_token: str
    token_type: str 