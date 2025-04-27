from collections import defaultdict
from typing import List, Dict
from backend.app.models.history import HistoryEntry

# In-memory storage for conversation history
# Structure: {session_id: [HistoryEntry, HistoryEntry, ...]}
conversation_history: Dict[str, List[HistoryEntry]] = defaultdict(list)

def save_history_entry(session_id: str, user_message: str, llm_response: str) -> HistoryEntry:
    """Saves a new entry to the conversation history for a given session."""
    entry = HistoryEntry(
        session_id=session_id,
        user_message=user_message,
        llm_response=llm_response
    )
    conversation_history[session_id].append(entry)
    print(f"History entry saved for session {session_id}. Total entries: {len(conversation_history[session_id])}") # Debug print
    return entry

def get_history(session_id: str) -> List[HistoryEntry]:
    """Retrieves the conversation history for a given session."""
    print(f"Retrieving history for session {session_id}. Found {len(conversation_history[session_id])} entries.") # Debug print
    return conversation_history[session_id]

def clear_history(session_id: str = None):
    """Clears the history for a specific session or all sessions if no session_id is provided."""
    if session_id:
        if session_id in conversation_history:
            del conversation_history[session_id]
            print(f"History cleared for session {session_id}.")
        else:
            print(f"No history found for session {session_id} to clear.")
    else:
        conversation_history.clear()
        print("All conversation history cleared.")