from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.app.schemas.token import Token
from backend.app.core.security import verify_password, create_access_token
from backend.app.crud import user_crud # Import the CRUD module
from backend.app.db.session import get_db_session # Import the dependency

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Uses OAuth2PasswordRequestForm, which expects form data with keys:
    - username: The user's username.
    - password: The user's password.
    """
    # Use username from the form data to find the user
    user = await user_crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    # Identity for the token subject can be username or user ID (email, etc.)
    # Using username here as per TokenData schema expectation
    access_token = create_access_token(
        data={"sub": user.username} # 'sub' is standard claim for subject
    )
    return {"access_token": access_token, "token_type": "bearer"} 