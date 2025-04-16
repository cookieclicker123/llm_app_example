import asyncio
from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
from typing import AsyncGenerator

class MockLLMClient:
    """
    A mock LLM client for testing purposes. Provides deterministic responses.
    """
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Simulates generating a non-streaming response based on the prompt.
        """
        await asyncio.sleep(0.1) # Simulate network delay
        response_text = f"Mock response to: '{request.prompt}'"
        if request.prompt.lower() == "hello":
            response_text = "Mock Hi there!"

        return LLMResponse(
            response=response_text,
            request_id=f"mock_{request.session_id or 'req'}",
            model_name="mock-model-v1",
            finish_reason="stop"
        )

    async def stream_response(self, request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        Simulates generating a streaming response.
        Yields chunks of the response text.
        """
        response_text = f"Mock stream response to: '{request.prompt}'"
        if request.prompt.lower() == "hello stream":
            response_text = "Mock Stream: Hi there! How can I help?"

        words = response_text.split()
        for i, word in enumerate(words):
            await asyncio.sleep(0.05) # Simulate token generation delay
            yield word + (" " if i < len(words) - 1 else "")

# You can also define standalone functions adhering to the type aliases if preferred:
mock_llm_func: LLMFunction = MockLLMClient().generate_response
mock_llm_stream_func: LLMStreamingFunction = MockLLMClient().stream_response 