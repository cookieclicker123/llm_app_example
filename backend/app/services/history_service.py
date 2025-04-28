import redis.asyncio as redis
import logging
from typing import List, Optional
import uuid # Import uuid
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession
from fastapi import Depends, HTTPException, status # Import HTTPException, status

from backend.app.models.history import HistoryEntry
from backend.app.models.user import User # Import User model
from backend.app.crud import history_crud, session_crud # Import session_crud
from backend.app.schemas.session import SessionCreate # Import SessionCreate
from backend.app.core.dependencies import get_redis # Import from new location
from backend.app.models.session import ConversationSession # <-- ADD THIS IMPORT
# No longer get redis directly, it will be passed down from chat service
# from backend.app.db.session import get_db_session # We'll get db session from chat service

# In-memory storage (REMOVED)
# conversation_history: Dict[str, List[HistoryEntry]] = defaultdict(list)

logger = logging.getLogger(__name__)

# --- Helper to verify session ownership ---
async def _verify_session_owner(
    db: AsyncSession, session_uuid_str: str, current_user: User
) -> uuid.UUID:
    """Verifies session exists and belongs to the user. Returns session UUID object."""
    try:
        session_uuid = uuid.UUID(session_uuid_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID format.")

    db_session = await session_crud.get_session_by_session_uuid(db, session_uuid=session_uuid)
    
    if not db_session:
        # For get/clear, session must exist. For save, we might create it.
        # Let caller decide how to handle non-existence.
        return None # Indicate session doesn't exist

    if db_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this session.")
    
    return session_uuid # Return the validated UUID object


# --- Refactored Service Functions ---

async def save_history_entry(
    session_id_str: str, # Renamed to avoid clash with session_id var
    user_message: str,
    llm_response: str,
    redis_conn: redis.Redis,
    db: AsyncSession, # Add db session dependency
    current_user: User # Add current user dependency
) -> HistoryEntry:
    """Saves history to Redis & ensures session metadata exists in Postgres."""
    
    try:
        session_uuid = uuid.UUID(session_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID format.")

    # Ensure session metadata exists and belongs to user, create if not
    db_session = await session_crud.get_session_by_session_uuid(db, session_uuid=session_uuid)
    
    if not db_session:
        logger.info(f"No session metadata found for session {session_uuid}. Creating new entry.")
        session_data = SessionCreate(session_uuid=session_uuid, title=None) # Auto-generate title later?
        await session_crud.create_session(db, session_in=session_data, user_id=current_user.id)
    elif db_session.user_id != current_user.id:
        # This case should ideally not happen if get/clear verify first, but double-check
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to save to this session.")
    # else: session exists and belongs to user - proceed
    # Note: last_accessed_at is updated via onupdate in model

    entry = HistoryEntry(
        session_id=session_id_str, # Use the original string for HistoryEntry if needed
        user_message=user_message,
        llm_response=llm_response
    )
    try:
        await history_crud.add_history_entry(redis_conn, session_id_str, entry)
        logger.info(f"History entry saved to Redis for session {session_id_str}.")
        return entry
    except Exception as e:
        logger.error(f"Service error saving history to Redis for session {session_id_str}: {e}")
        raise

async def get_history(
    session_id_str: str,
    redis_conn: redis.Redis,
    db: AsyncSession, # Add db session dependency
    current_user: User # Add current user dependency
) -> List[HistoryEntry]:
    """Retrieves history from Redis after verifying ownership via Postgres."""
    
    session_uuid = await _verify_session_owner(db, session_id_str, current_user)
    if not session_uuid:
         # If session doesn't exist in DB, it shouldn't have history in Redis (or it's orphaned)
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        
    try:
        history = await history_crud.get_history(redis_conn, session_id_str)
        logger.info(f"Retrieved {len(history)} history entries from Redis for session {session_id_str}.")
        return history
    except Exception as e:
        logger.error(f"Service error retrieving history from Redis for session {session_id_str}: {e}")
        return []

async def clear_session_history( # Renamed for clarity
    session_id_str: str,
    redis_conn: redis.Redis,
    db: AsyncSession, # Add db session dependency
    current_user: User # Add current user dependency
):
    """Clears history from Redis AND deletes session metadata from Postgres."""
    
    try:
        session_uuid = uuid.UUID(session_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID format.")

    db_session = await session_crud.get_session_by_session_uuid(db, session_uuid=session_uuid)
    
    if not db_session:
        # If session doesn't exist in DB, no need to clear anything
         logger.warning(f"Attempted to clear non-existent session: {session_uuid}")
         # Raise 404 to indicate the resource doesn't exist
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    if db_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to clear this session.")

    # Delete from Postgres first (or wrap in transaction if needed)
    try:
        await session_crud.delete_session(db, db_session=db_session)
        logger.info(f"Deleted session metadata from Postgres for session {session_uuid}")
    except Exception as e:
         logger.error(f"Service error deleting session metadata for {session_uuid}: {e}")
         # Decide if we should proceed to clear Redis or stop here
         raise

    # Clear from Redis
    try:
        await history_crud.clear_session_history(redis_conn, session_id_str)
        # Logging is handled within the history_crud function
    except Exception as e:
        logger.error(f"Service error clearing history from Redis for session {session_id_str}: {e}")
        # Consider potential inconsistency if Postgres delete succeeded but Redis clear failed
        raise

# --- New Function ---
async def list_user_sessions(
    db: AsyncSession, current_user: User, skip: int = 0, limit: int = 100
) -> list[ConversationSession]: # Return the DB model directly
    """Lists session metadata for the current user."""
    sessions = await session_crud.get_sessions_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return sessions

# --- Removed old clear_history ---
# async def clear_history(...): previous implementation