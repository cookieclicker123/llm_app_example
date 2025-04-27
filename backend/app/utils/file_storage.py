import json
from pathlib import Path
import logging

import aiofiles
from pydantic import ValidationError

from app.models.history import ConversationHistory

logger = logging.getLogger(__name__)

async def load_conversation_history(session_id: str, storage_path: Path) -> ConversationHistory | None:
    """Loads conversation history for a given session_id from a JSON file.

    Args:
        session_id: The ID of the session to load.
        storage_path: The directory where history files are stored.

    Returns:
        A ConversationHistory object if the file exists and is valid, otherwise None.
    """
    history_file = storage_path / f"history_{session_id}.json"
    if not history_file.exists():
        logger.debug(f"No history file found for session_id: {session_id}")
        return None

    try:
        async with aiofiles.open(history_file, mode='r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            history = ConversationHistory.model_validate(data)
            logger.debug(f"Successfully loaded history for session_id: {session_id}")
            return history
    except FileNotFoundError:
        logger.debug(f"History file disappeared before reading for session_id: {session_id}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from history file: {history_file}")
        return None
    except ValidationError as e:
        logger.error(f"Validation error loading history file {history_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading history file {history_file}: {e}")
        return None

async def save_conversation_history(history: ConversationHistory, storage_path: Path) -> None:
    """Saves the conversation history object to a JSON file.

    Args:
        history: The ConversationHistory object to save.
        storage_path: The directory where history files should be stored.
    """
    storage_path.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    history_file = storage_path / f"history_{history.session_id}.json"

    try:
        # Use model_dump_json for Pydantic v2, ensuring correct serialization
        history_json = history.model_dump_json(indent=2)
        async with aiofiles.open(history_file, mode='w', encoding='utf-8') as f:
            await f.write(history_json)
        logger.debug(f"Successfully saved history for session_id: {history.session_id}")
    except Exception as e:
        logger.error(f"Error saving history file {history_file}: {e}")
        # Depending on requirements, might want to raise exception here 