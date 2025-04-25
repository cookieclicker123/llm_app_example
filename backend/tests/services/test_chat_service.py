import pytest
import pytest_asyncio
from pathlib import Path

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
from backend.app.services.chat_service import handle_chat_request, handle_chat_stream
from backend.tests.mocks.mock_llm import (
    create_mock_llm_generate_func,
    create_mock_llm_stream_func,
    DEFAULT_NOT_FOUND_RESPONSE
)

# Define the path to the fixtures directory relative to this test file
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
QA_FILE_PATH = FIXTURES_DIR / "mock_qa_pairs.json"

# --- Fixtures --- #

@pytest.fixture
def mock_generate_func() -> LLMFunction:
    """Provides an instance of the mock generate function from our mock factory."""
    # Use high speed for tests to minimize delay
    return create_mock_llm_generate_func(qa_file_path=QA_FILE_PATH, emulation_speed_cps=10000)

@pytest.fixture
def mock_stream_func() -> LLMStreamingFunction:
    """Provides an instance of the mock stream function from our mock factory."""
    # Use high speed for tests to minimize delay
    return create_mock_llm_stream_func(qa_file_path=QA_FILE_PATH, emulation_speed_cps=10000)

# --- Test Cases --- #

@pytest.mark.asyncio
async def test_handle_chat_request_success(mock_generate_func: LLMFunction):
    """Test handle_chat_request successfully calls the injected LLM function."""
    test_prompt = "Hello"
    request = LLMRequest(prompt=test_prompt, session_id="test_session_gen")

    # Call the service function, injecting the mock LLM function
    response = await handle_chat_request(request, mock_generate_func)

    assert isinstance(response, LLMResponse)
    # Check response content based on mock_qa_pairs.json
    assert response.response == "Mock Hi there! This is a predefined answer."
    assert response.model_name == "mock-qa-gen-v1"
    assert response.request_id is not None
    assert "test_session_gen" in response.request_id

@pytest.mark.asyncio
async def test_handle_chat_request_not_found(mock_generate_func: LLMFunction):
    """Test handle_chat_request with a prompt not in the mock data."""
    test_prompt = "This prompt definitely does not exist"
    request = LLMRequest(prompt=test_prompt, session_id="test_session_nf")

    response = await handle_chat_request(request, mock_generate_func)

    assert isinstance(response, LLMResponse)
    assert response.response == DEFAULT_NOT_FOUND_RESPONSE # Check default mock response

@pytest.mark.asyncio
async def test_handle_chat_stream_success(mock_stream_func: LLMStreamingFunction):
    """Test handle_chat_stream successfully yields chunks from the injected LLM function."""
    test_prompt = "Tell me a joke"
    expected_full_response = "Why don't scientists trust atoms? Because they make up everything! (Mock Joke)"
    request = LLMRequest(prompt=test_prompt, session_id="test_session_stream")

    chunks = []
    # Call the service function, injecting the mock streaming LLM function
    async for chunk in handle_chat_stream(request, mock_stream_func):
        assert isinstance(chunk, StreamingChunk) # Should be strings
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == expected_full_response

@pytest.mark.asyncio
async def test_handle_chat_stream_not_found(mock_stream_func: LLMStreamingFunction):
    """Test handle_chat_stream with a prompt not in the mock data."""
    test_prompt = "Another prompt that surely does not exist"
    request = LLMRequest(prompt=test_prompt, session_id="test_session_stream_nf")

    chunks = []
    async for chunk in handle_chat_stream(request, mock_stream_func):
        assert isinstance(chunk, StreamingChunk)
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == DEFAULT_NOT_FOUND_RESPONSE

# Add more tests later for error handling within the service if needed 