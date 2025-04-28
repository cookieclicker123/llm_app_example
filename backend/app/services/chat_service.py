import logging
from typing import AsyncGenerator, List, Dict
from datetime import datetime, UTC # Import datetime components
import time # Import time for performance counter
import uuid # Import uuid
from pathlib import Path # Ensure Path is imported
from fastapi import Depends # Import Depends
import redis.asyncio as redis # Import redis
# Add DB and User imports
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.db.session import get_db_session
from backend.app.models.history import HistoryEntry

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
from backend.app.core.config import get_settings, Settings
# Update history service import path if necessary
from backend.app.services import history_service # Assuming history_service is in services
from backend.app.core.dependencies import get_redis # Import redis dependency
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# --- Helper Function to Format History --- #
def format_history_for_llm(history: List[HistoryEntry]) -> List[Dict[str, str]]:
    """Formats history list from Redis into the list-of-dicts format for Ollama."""
    formatted = []
    for entry in history:
        formatted.append({"role": "user", "content": entry.user_message})
        # Check if llm_response exists and is not None before appending
        if entry.llm_response is not None:
            formatted.append({"role": "assistant", "content": entry.llm_response})
        # Else: Maybe log a warning? Or just skip the assistant turn if response is missing.
    return formatted

# Define the directory for saving JSON responses - NOW READ FROM SETTINGS
# SAVE_DIR = "backend/tmp/json_sessions"

async def handle_chat_request(
    request: LLMRequest,
    llm_generate_func: LLMFunction, # Dependency: The function to call the LLM
    app_settings: Settings = Depends(get_settings), # Dependency: Inject settings
    redis_conn: redis.Redis = Depends(get_redis), # Dependency: Inject Redis
    db: AsyncSession = Depends(get_db_session), # Dependency: Inject DB Session
    current_user: User = Depends() # Placeholder: Add Depends(get_current_active_user) later
) -> LLMResponse:
    """
    Handles a non-streaming chat request, records metadata, and returns a rich LLMResponse.
    It now correctly processes output from both mock (dict) and real (partial LLMResponse) generators.
    Uses injected settings for configuration like save directory.

    Args:
        request: The user's request data.
        llm_generate_func: The specific LLM function (mock or real) to use.
        app_settings: The injected settings object.
        redis_conn: The injected Redis connection.
        db: The injected DB session.
        current_user: The current active user.

    Returns:
        A rich LLMResponse object containing the response and metadata.
    """
    logger.info(f"Handling chat request for session: {request.session_id} by user {current_user.username}")
    response_id = uuid.uuid4()
    created_at = datetime.now(UTC)
    start_time = time.perf_counter()

    # Retrieve existing history for the session, handle if not found
    try:
        retrieved_history = await history_service.get_history(
            session_id_str=request.session_id,
            redis_conn=redis_conn,
            db=db,
            current_user=current_user
        )
        history_for_llm = format_history_for_llm(retrieved_history)
        logger.info(f"Retrieved {len(retrieved_history)} history entries for session {request.session_id}.")
    except HTTPException as e:
        if e.status_code == 404:
            logger.info(f"Session {request.session_id} not found, starting new history.")
            retrieved_history = [] # Start with empty history
            history_for_llm = []
        else:
            # Re-raise other HTTP exceptions (like 403 Forbidden)
            logger.error(f"Error retrieving history for session {request.session_id}: {e.detail}")
            raise
    except Exception as e:
        # Handle unexpected errors during history retrieval
        logger.error(f"Unexpected error retrieving history for session {request.session_id}: {e}", exc_info=True)
        # Decide how to proceed: maybe raise 500 or proceed with empty history?
        # For now, let's raise 500 as something unexpected happened
        raise HTTPException(status_code=500, detail="Error retrieving session history.")

    # Future enhancements:
    # 2. Format prompt with history and system prompt (LLM client responsibility?)
    # 3. Add pre/post processing logic

    # --- Call the LLM function --- #
    # Pass history to the LLM function (assuming it accepts a 'history' argument)
    # Pass a copy to prevent mutation issues if the underlying history store is modified during the call
    raw_llm_output = await llm_generate_func(request, history=retrieved_history.copy())

    # --- Record timing --- #
    end_time = time.perf_counter()
    completed_at = datetime.now(UTC)
    elapsed_time_ms = (end_time - start_time) * 1000

    # --- Extract required data from raw output --- #
    response_text = "Error: Could not determine response text."
    # Initialize model_name from the request, as it's guaranteed to be there now
    model_name = request.model_name 
    finish_reason = None

    # Try to get more specific info from the actual LLM call output
    if isinstance(raw_llm_output, LLMResponse): 
        logger.debug("Processing LLMResponse object from llm_generate_func.")
        response_text = raw_llm_output.response
        # Update model_name only if the raw output explicitly provides it
        if raw_llm_output.model_name:
            model_name = raw_llm_output.model_name 
        finish_reason = getattr(raw_llm_output, 'finish_reason', None)

    elif isinstance(raw_llm_output, dict): 
        logger.debug("Processing dict object from llm_generate_func.")
        response_text = raw_llm_output.get("response", "Error: Missing 'response' key.")
        # Update model_name only if the raw output explicitly provides it
        model_name_from_output = raw_llm_output.get("model_name")
        if model_name_from_output:
            model_name = model_name_from_output
        finish_reason = raw_llm_output.get("finish_reason")

    else:
        logger.error(f"Unexpected output type from llm_generate_func: {type(raw_llm_output)}")
        response_text = f"Error: Unexpected LLM output type '{type(raw_llm_output).__name__}'."
        # Keep model_name from the original request

    # --- Construct the final, rich LLMResponse --- #
    llm_response = LLMResponse(
        response_id=response_id,
        request=request, 
        response=response_text,
        created_at=created_at,
        completed_at=completed_at,
        elapsed_time_ms=elapsed_time_ms,
        model_name=model_name, # Now guaranteed to be non-null
        finish_reason=finish_reason
    )

    # --- Save request/response pair to history (passing db/user) --- #
    try:
        await history_service.save_history_entry(
            session_id_str=request.session_id,
            user_message=request.prompt,
            llm_response=llm_response.response, # Save the actual response text
            redis_conn=redis_conn,
            db=db,
            current_user=current_user
        )
        logger.info(f"Saved interaction to history for session {request.session_id}.")
    except Exception as e:
        # Let exception propagate if it's an error during session creation/check
        logger.exception(f"Failed to save interaction to history for session {request.session_id}.")
        raise 

    # --- Save the response to JSON --- #
    save_dir = app_settings.CHAT_RESPONSE_SAVE_DIR
    logger.info(f"Attempting to save response {llm_response.response_id} to JSON.")
    try:
        # Log the absolute path we intend to use inside the container
        # Assume base dir is /app - path joining handled by Path object now
        # Use resolve() to get absolute path robustly
        container_base_path = Path("/app")
        # Ensure the save_dir from settings is treated relative to the container base
        intended_save_path = container_base_path / save_dir
        logger.info(f"Ensuring directory exists: {intended_save_path.resolve()}")

        intended_save_path.mkdir(parents=True, exist_ok=True) # Create directory if it doesn't exist

        # Use response_id and timestamp for a unique filename
        timestamp_str = created_at.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp_str}_{llm_response.response_id}.json"
        filepath = intended_save_path / filename
        logger.info(f"Attempting to write JSON to: {filepath.resolve()}")

        with open(filepath, 'w') as f:
            f.write(llm_response.model_dump_json(indent=2))
        logger.info(f"Successfully saved chat response to {filepath.resolve()}")

    except Exception as e:
        logger.exception(f"CRITICAL: Failed to save chat response {llm_response.response_id} to JSON.")

    # Future enhancements:
    # 1. Save request/response pair (llm_response object) to history (using crud) -> Handled above now
    # 2. Implement JSON saving logic here -> This is already done

    logger.info(f"Successfully handled chat request {response_id} for session: {request.session_id}")
    return llm_response

async def handle_chat_stream(
    request: LLMRequest,
    llm_stream_func: LLMStreamingFunction, # Dependency: The streaming LLM function
    redis_conn: redis.Redis = Depends(get_redis), # Dependency: Inject Redis
    db: AsyncSession = Depends(get_db_session), # Dependency: Inject DB Session
    current_user: User = Depends() # Placeholder: Add Depends(get_current_active_user) later
) -> AsyncGenerator[StreamingChunk, None]:
    """
    Handles a streaming chat request by calling the provided streaming LLM function.
    Retrieves history and passes it to the streaming function.

    Args:
        request: The user's request data.
        llm_stream_func: The specific streaming LLM function (mock or real) to use.
        redis_conn: The injected Redis connection.
        db: The injected DB session.
        current_user: The current active user.

    Yields:
        StreamingChunk: Chunks of the LLM response.
    """
    logger.info(f"Handling chat stream for session: {request.session_id} by user {current_user.username}")

    # 1. Retrieve conversation history using request.session_id (passing db/user)
    aggregated_response = "" # To store the full response for history saving
    try:
        retrieved_history = await history_service.get_history(
            session_id_str=request.session_id, # Pass session_id as string
            redis_conn=redis_conn, 
            db=db, 
            current_user=current_user
        )
        logger.info(f"Retrieved {len(retrieved_history)} history entries for streaming session {request.session_id}.")
    except HTTPException as e:
        # If session not found (404) or forbidden (403), let it propagate
        if e.status_code == status.HTTP_404_NOT_FOUND or e.status_code == status.HTTP_403_FORBIDDEN:
             logger.warning(f"History retrieval failed for stream session {request.session_id}: {e.detail}")
             raise e 
        # For other errors, maybe default to empty list? Or raise?
        logger.exception(f"Unexpected error retrieving history for streaming session {request.session_id}.")
        raise # Re-raising generic exceptions for now
        # retrieved_history = [] 
    except Exception as e:
        logger.exception(f"Unexpected error retrieving history for streaming session {request.session_id}.")
        raise # Re-raise other unexpected errors
        # retrieved_history = [] 

    # Call the injected streaming LLM function and yield chunks
    try:
        # The ollama client yields string chunks
        async for text_chunk in llm_stream_func(request, history=retrieved_history.copy()): # Pass formatted history? No, ollama_client formats it.
            # Wrap the string chunk in our StreamingChunk model
            chunk_model = StreamingChunk(session_id=request.session_id, content=text_chunk, type="content")
            # Yield the model dump as a JSON string, followed by newline for SSE format
            yield chunk_model.model_dump_json() + "\n"
            # Aggregate the response content from chunks
            aggregated_response += text_chunk # Aggregate the raw text
    except Exception as e:
         logger.exception(f"Error during LLM stream for session {request.session_id}.")
         # Yield a StreamingChunk object for the error, encoded as JSON
         error_chunk = StreamingChunk(session_id=request.session_id, content=f"Error during stream: {e}", type="error")
         yield error_chunk.model_dump_json() + "\n"
         return # Stop the generator

    # --- Save full interaction after successful stream --- #
    if aggregated_response:
        try:
            await history_service.save_history_entry(
                session_id_str=request.session_id,
                user_message=request.prompt,
                llm_response=aggregated_response,
                redis_conn=redis_conn,
                db=db,
                current_user=current_user
            )
            logger.info(f"Saved full streamed interaction to history for session {request.session_id}.")
        except Exception as e:
            logger.exception(f"Failed to save full streamed interaction to history for session {request.session_id}.")
            # Don't raise here, as the stream completed for the user

    logger.info(f"Finished handling chat stream for session: {request.session_id}") 