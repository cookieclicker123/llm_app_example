import redis.asyncio as redis
import logging
from typing import List
from fastapi import Depends # Import Depends

from backend.app.models.history import HistoryEntry
from backend.app.crud import history_crud # Import the CRUD functions
from backend.app.main import get_redis # Import the Redis dependency provider

# In-memory storage (REMOVED)
# conversation_history: Dict[str, List[HistoryEntry]] = defaultdict(list)

logger = logging.getLogger(__name__)

async def save_history_entry(
    session_id: str,
    user_message: str,
    llm_response: str,
    redis_conn: redis.Redis = Depends(get_redis) # Inject Redis connection
) -> HistoryEntry:
    """Constructs a HistoryEntry and saves it to Redis via CRUD layer."""
    entry = HistoryEntry(
        session_id=session_id,
        user_message=user_message,
        llm_response=llm_response
    )
    try:
        await history_crud.add_history_entry(redis_conn, session_id, entry)
        logger.info(f"History entry saved to Redis for session {session_id}.")
        return entry
    except Exception as e:
        # Log the exception from the CRUD layer if needed, or let it propagate
        logger.error(f"Service error saving history for session {session_id}: {e}")
        raise # Re-raise the exception

async def get_history(
    session_id: str,
    redis_conn: redis.Redis = Depends(get_redis) # Inject Redis connection
) -> List[HistoryEntry]:
    """Retrieves the conversation history for a given session from Redis via CRUD layer."""
    try:
        history = await history_crud.get_history(redis_conn, session_id)
        logger.info(f"Retrieved {len(history)} history entries from Redis for session {session_id}.")
        return history
    except Exception as e:
        logger.error(f"Service error retrieving history for session {session_id}: {e}")
        # Depending on requirements, might return empty list or re-raise
        return [] # Return empty list on error for now

async def clear_history(
    session_id: str,
    redis_conn: redis.Redis = Depends(get_redis) # Inject Redis connection
):
    """Clears the history for a specific session in Redis via CRUD layer."""
    # Note: Clearing *all* history is deliberately omitted here for safety.
    # It should be handled via admin/ops procedures.
    if not session_id:
        logger.warning("Attempted to call clear_history without a session_id.")
        return # Or raise an error
    
    try:
        await history_crud.clear_session_history(redis_conn, session_id)
        # Logging is handled within the CRUD function
    except Exception as e:
        logger.error(f"Service error clearing history for session {session_id}: {e}")
        raise # Re-raise the exception