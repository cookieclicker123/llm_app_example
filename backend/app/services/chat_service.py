import logging
from typing import AsyncGenerator

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction

logger = logging.getLogger(__name__)

async def handle_chat_request(
    request: LLMRequest,
    llm_generate_func: LLMFunction # Dependency: The function to call the LLM
) -> LLMResponse:
    """
    Handles a non-streaming chat request by calling the provided LLM function.

    Args:
        request: The user's request data.
        llm_generate_func: The specific LLM function (mock or real) to use.

    Returns:
        The LLM response.
    """
    logger.info(f"Handling chat request for session: {request.session_id}")

    # Future enhancements:
    # 1. Retrieve conversation history using request.session_id (from crud)
    # 2. Format prompt with history and system prompt
    # 3. Add pre/post processing logic

    # Call the injected LLM function
    llm_response = await llm_generate_func(request)

    # Future enhancements:
    # 1. Save request/response pair to history (using crud)

    logger.info(f"Successfully handled chat request for session: {request.session_id}")
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