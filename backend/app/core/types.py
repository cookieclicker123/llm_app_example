from typing import Callable, Coroutine, Any, AsyncGenerator
from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk

# Type alias for a standard LLM call (request -> response)
LLMFunction = Callable[[LLMRequest], Coroutine[Any, Any, LLMResponse]]

# Type alias for a streaming LLM call (request -> async generator of chunks)
LLMStreamingFunction = Callable[[LLMRequest], AsyncGenerator[StreamingChunk, None]]

# Type alias for a callback function to handle streaming chunks
# Takes the chunk as input, returns None or awaitable None
OnChunkCallback = Callable[[StreamingChunk], Coroutine[Any, Any, None] | None] 