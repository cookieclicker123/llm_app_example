import redis.asyncio as redis
import logging
from typing import List
from backend.app.models.history import HistoryEntry

logger = logging.getLogger(__name__)

# Define a prefix for session keys to avoid potential collisions in Redis
SESSION_KEY_PREFIX = "session:"

def _get_session_key(session_id: str) -> str:
    """Constructs the Redis key for a given session ID."""
    return f"{SESSION_KEY_PREFIX}{session_id}"

async def add_history_entry(redis_conn: redis.Redis, session_id: str, entry: HistoryEntry):
    """Adds a new history entry (serialized as JSON) to the beginning of a Redis list.

    Args:
        redis_conn: An active async Redis connection/client.
        session_id: The ID of the session.
        entry: The HistoryEntry object to add.
    """
    session_key = _get_session_key(session_id)
    try:
        # Serialize the Pydantic model to JSON string
        entry_json = entry.model_dump_json()
        # LPUSH adds the element to the head of the list
        await redis_conn.lpush(session_key, entry_json)
        logger.debug(f"Added history entry to Redis list: {session_key}")
    except Exception as e:
        logger.error(f"Failed to add history entry to Redis for key {session_key}: {e}")
        # Consider re-raising or specific error handling
        raise

async def get_history(redis_conn: redis.Redis, session_id: str) -> List[HistoryEntry]:
    """Retrieves the entire conversation history for a session from a Redis list.

    Args:
        redis_conn: An active async Redis connection/client.
        session_id: The ID of the session.

    Returns:
        A list of HistoryEntry objects, ordered from oldest to newest.
    """
    session_key = _get_session_key(session_id)
    history = []
    try:
        # LRANGE 0 -1 retrieves all elements from the list
        # Note: Redis lists store elements in insertion order. LPUSH adds to the head.
        # So, LRANGE retrieves them from newest (head) to oldest (tail).
        entries_json = await redis_conn.lrange(session_key, 0, -1)
        logger.debug(f"Retrieved {len(entries_json)} entries from Redis list: {session_key}")
        
        # Deserialize JSON strings back into HistoryEntry objects
        for entry_json in entries_json:
            try:
                entry = HistoryEntry.model_validate_json(entry_json)
                history.append(entry)
            except Exception as e:
                logger.error(f"Failed to deserialize history entry from Redis key {session_key}: {entry_json}. Error: {e}")
                # Decide whether to skip corrupted entries or raise an error
                continue # Skip corrupted entry for now
        
        # Reverse the list to maintain chronological order (oldest first)
        history.reverse()
        return history

    except Exception as e:
        logger.error(f"Failed to retrieve history from Redis for key {session_key}: {e}")
        # Consider re-raising or specific error handling
        raise

async def clear_session_history(redis_conn: redis.Redis, session_id: str):
    """Deletes the conversation history list for a specific session.

    Args:
        redis_conn: An active async Redis connection/client.
        session_id: The ID of the session to clear.
    """
    session_key = _get_session_key(session_id)
    try:
        deleted_count = await redis_conn.delete(session_key)
        if deleted_count > 0:
            logger.info(f"Cleared history for session {session_id} (Redis key: {session_key})")
        else:
            logger.debug(f"No history found in Redis to clear for session {session_id} (Redis key: {session_key})")
    except Exception as e:
        logger.error(f"Failed to clear history in Redis for key {session_key}: {e}")
        # Consider re-raising or specific error handling
        raise

# Note: A function to clear *all* history (like FLUSHDB or key scanning) is potentially dangerous 
# and usually not exposed directly at this level. It's better handled via Redis admin tools or specific operational scripts. 