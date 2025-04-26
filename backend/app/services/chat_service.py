import logging
from typing import AsyncGenerator
from datetime import datetime, UTC # Import datetime components
import time # Import time for performance counter
import uuid # Import uuid
from pathlib import Path # Ensure Path is imported
from fastapi import Depends # Import Depends

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
from backend.app.core.config import get_settings, Settings

logger = logging.getLogger(__name__)

# Define the directory for saving JSON responses - NOW READ FROM SETTINGS
# SAVE_DIR = "backend/tmp/json_sessions"

async def handle_chat_request(
    request: LLMRequest,
    llm_generate_func: LLMFunction, # Dependency: The function to call the LLM
    app_settings: Settings = Depends(get_settings) # Dependency: Inject settings
) -> LLMResponse:
    """
    Handles a non-streaming chat request, records metadata, and returns a rich LLMResponse.
    It now correctly processes output from both mock (dict) and real (partial LLMResponse) generators.
    Uses injected settings for configuration like save directory.

    Args:
        request: The user's request data.
        llm_generate_func: The specific LLM function (mock or real) to use.
        app_settings: The injected settings object.

    Returns:
        A rich LLMResponse object containing the response and metadata.
    """
    logger.info(f"Handling chat request for session: {request.session_id}")
    response_id = uuid.uuid4()
    created_at = datetime.now(UTC)
    start_time = time.perf_counter()

    # Future enhancements:
    # 1. Retrieve conversation history using request.session_id (from crud)
    # 2. Format prompt with history and system prompt
    # 3. Add pre/post processing logic

    # --- Call the LLM function --- #
    raw_llm_output = await llm_generate_func(request)

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
    # 1. Save request/response pair (llm_response object) to history (using crud)
    # 2. Implement JSON saving logic here

    logger.info(f"Successfully handled chat request {response_id} for session: {request.session_id}")
    return llm_response

async def handle_chat_stream(
    request: LLMRequest,
    llm_stream_func: LLMStreamingFunction # Dependency: The streaming LLM function
) -> AsyncGenerator[StreamingChunk, None]:
    """
    Handles a streaming chat request by calling the provided streaming LLM function.

    Args:
        request: The user's request data.
        llm_stream_func: The specific streaming LLM function (mock or real) to use.

    Yields:
        StreamingChunk: Chunks of the LLM response.
    """
    logger.info(f"Handling chat stream for session: {request.session_id}")

    # Future enhancements (similar to non-streaming)

    # Call the injected streaming LLM function and yield chunks
    async for chunk in llm_stream_func(request):
        yield chunk

    # Future enhancements (logging completion, saving full response?)
    logger.info(f"Finished handling chat stream for session: {request.session_id}") 