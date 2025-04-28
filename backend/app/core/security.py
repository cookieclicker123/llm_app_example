from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.app.core.config import settings
from backend.app.schemas.token import TokenData
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db_session
from backend.app.crud import user_crud
from backend.app.models.user import User

# Password Hashing Context
# Using bcrypt, which is the recommended default
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
# tokenUrl should point to our actual login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

async def decode_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Decodes the JWT token and returns token data (e.g., user ID/username)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

# Function to get the current user from the token
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Decodes token, retrieves user from DB based on username in token.
    
    Raises:
        HTTPException 401: If token is invalid or user not found.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials (no username)",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (JWTError)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_crud.get_user_by_username(db, username=username)
    if user is None:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Or 404, but 401 implies invalid token overall
            detail="User not found for token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Dependency to get the current *active* user
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Checks if the user retrieved from the token is active.
    
    Raises:
        HTTPException 400: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user 