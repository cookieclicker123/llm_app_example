import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from backend.app.db.session import get_db_session
from backend.app.models.user import User
from backend.app.core.security import get_current_active_user
from backend.app.schemas.session import SessionRead # Import the response schema
from backend.app.services import history_service # Import the service function

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[SessionRead])
async def list_current_user_sessions(
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of sessions to return"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve metadata for the current user's conversation sessions,
    ordered by most recently accessed.
    """
    logger.info(f"User {current_user.username} requested session list (skip={skip}, limit={limit}).")
    # Call the service function which handles fetching sessions for the user
    # The service function currently returns DB models, which Pydantic
    # automatically converts to SessionRead thanks to from_attributes=True
    sessions = await history_service.list_user_sessions(
        db=db, current_user=current_user, skip=skip, limit=limit
    )
    logger.info(f"Returning {len(sessions)} sessions for user {current_user.username}.")
    return sessions 