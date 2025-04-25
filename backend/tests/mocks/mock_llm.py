import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator, Dict

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction

DEFAULT_EMULATION_SPEED_CPS = 50 # Characters per second
DEFAULT_NOT_FOUND_RESPONSE = "Sorry, I don't have a mock answer for that prompt."

def _load_qa_data(qa_file_path: str | Path) -> Dict[str, str]:
    """Helper function to load and prepare QA data."""
    qa_path = Path(qa_file_path)
    if not qa_path.is_file():
        raise FileNotFoundError(f"QA file not found at: {qa_path}")

    with open(qa_path, 'r') as f:
        qa_pairs: Dict[str, str] = json.load(f)

    # Return lowercase keys for case-insensitive lookup
    return {k.lower(): v for k, v in qa_pairs.items()}

def create_mock_llm_generate_func(
    qa_file_path: str | Path,
    emulation_speed_cps: int = DEFAULT_EMULATION_SPEED_CPS # Speed affects delay slightly
) -> LLMFunction:
    """
    Factory function that creates a mock LLM function for generating full responses.

    Args:
        qa_file_path: Path to the JSON file containing question-answer pairs.
        emulation_speed_cps: Simulated processing speed (adds minor delay).

    Returns:
        An async function conforming to the LLMFunction type alias.
    """
    _lowercase_qa = _load_qa_data(qa_file_path)
    _base_delay = 0.5 / max(1, emulation_speed_cps) # Small delay based on speed

    async def generate_response(request: LLMRequest) -> LLMResponse:
        """
        The actual mock LLM function that generates a response.
        """
        prompt_lower = request.prompt.lower()
        response_text = _lowercase_qa.get(prompt_lower, DEFAULT_NOT_FOUND_RESPONSE)

        # Simulate some base processing time
        await asyncio.sleep(_base_delay)

        return LLMResponse(
            response=response_text,
            request_id=f"mock_gen_{request.session_id or 'req123'}",
            model_name="mock-qa-gen-v1",
            finish_reason="stop"
            # created_at is handled by default_factory
        )

    return generate_response

def create_mock_llm_stream_func(
    qa_file_path: str | Path,
    emulation_speed_cps: int = DEFAULT_EMULATION_SPEED_CPS
) -> LLMStreamingFunction:
    """
    Factory function that creates a mock LLM function for streaming responses.

    Args:
        qa_file_path: Path to the JSON file containing question-answer pairs.
        emulation_speed_cps: Simulated streaming speed in characters per second.

    Returns:
        An async function conforming to the LLMStreamingFunction type alias.
    """
    _lowercase_qa = _load_qa_data(qa_file_path)
    _char_delay = 1.0 / max(1, emulation_speed_cps)

    async def stream_response(request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """
        The actual mock LLM function that streams a response.
        """
        prompt_lower = request.prompt.lower()
        response_text = _lowercase_qa.get(prompt_lower, DEFAULT_NOT_FOUND_RESPONSE)

        # Stream character by character with simulated delay
        for char in response_text:
            yield char
            await asyncio.sleep(_char_delay)

    return stream_response 