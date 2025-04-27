import pytest
import pytest_asyncio
from pathlib import Path
from uuid import UUID # Import UUID
from datetime import datetime # Import datetime
from unittest.mock import patch, call # Added patch and call

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
from backend.app.services.chat_service import handle_chat_request, handle_chat_stream
from backend.app.core.config import Settings # Import Settings
from backend.tests.mocks.mock_llm import (
    create_mock_llm_generate_func,
    create_mock_llm_stream_func,
    DEFAULT_NOT_FOUND_RESPONSE
)
# Import history service functions for testing
from backend.app.services.history_service import get_history, clear_history

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

@pytest.fixture
def test_settings() -> Settings:
    """Provides a Settings instance for service tests."""
    # Create a basic settings object. We could modify paths here if needed for specific tests.
    return Settings()

# --- Test Cases --- #

@pytest.mark.asyncio
async def test_handle_chat_request_success(mock_generate_func: LLMFunction, test_settings: Settings):
    """Test handle_chat_request successfully calls the injected LLM function and returns a rich LLMResponse."""
    test_prompt = "Hello"
    session_id = "test_session_gen"
    request = LLMRequest(prompt=test_prompt, session_id=session_id, model_name="test-model-svc")

    # Call the service function, injecting the mock LLM function AND settings
    response = await handle_chat_request(request, mock_generate_func, test_settings)

    # --- Assertions for the rich LLMResponse --- #
    assert isinstance(response, LLMResponse)
    assert response.response == "Mock Hi there! This is a predefined answer."
    assert response.model_name == "mock-qa-gen-v1"
    assert response.finish_reason == "stop"

    # Check the new fields
    assert isinstance(response.response_id, UUID)
    assert response.request == request # Should match the input request object
    assert isinstance(response.created_at, datetime)
    assert isinstance(response.completed_at, datetime)
    assert isinstance(response.elapsed_time_ms, float)
    assert response.elapsed_time_ms >= 0

    # Add assertion for request model name
    assert response.request.model_name == "test-model-svc"

@pytest.mark.asyncio
async def test_handle_chat_request_not_found(mock_generate_func: LLMFunction, test_settings: Settings):
    """Test handle_chat_request with a prompt not in the mock data."""
    test_prompt = "This prompt definitely does not exist"
    session_id = "test_session_nf"
    request = LLMRequest(prompt=test_prompt, session_id=session_id, model_name="test-model-svc-nf")

    response = await handle_chat_request(request, mock_generate_func, test_settings)

    assert isinstance(response, LLMResponse)
    assert response.response == DEFAULT_NOT_FOUND_RESPONSE
    assert response.model_name == "mock-qa-gen-v1"
    # Check essential metadata is still present
    assert isinstance(response.response_id, UUID)
    assert response.request == request
    assert isinstance(response.created_at, datetime)
    assert isinstance(response.completed_at, datetime)
    assert isinstance(response.elapsed_time_ms, float)

    # Add assertion for request model name
    assert response.request.model_name == "test-model-svc-nf"

@pytest.mark.asyncio
async def test_handle_chat_request_with_history(mock_generate_func: LLMFunction, test_settings: Settings):
    """Test that handle_chat_request retrieves and passes history correctly on subsequent calls."""
    session_id = "test_session_hist"
    model_name = "test-hist-model"
    prompt1 = "Hello" # Exists in mock_qa_pairs.json
    response1_expected = "Mock Hi there! This is a predefined answer."
    prompt2 = "How are you?" # Exists in mock_qa_pairs.json
    response2_expected = "I'm fine, thank you."

    # Ensure clean state for the session
    clear_history(session_id)

    try:
        # --- First Request --- # 
        request1 = LLMRequest(prompt=prompt1, session_id=session_id, model_name=model_name)
        print(f"\n--- Making first request for session {session_id} ---")
        response1 = await handle_chat_request(request1, mock_generate_func, test_settings)
        assert response1.response == response1_expected

        # Verify history was saved
        saved_history = get_history(session_id)
        assert len(saved_history) == 1
        assert saved_history[0].user_message == prompt1
        assert saved_history[0].llm_response == response1_expected
        print(f"--- History after first request for session {session_id} has {len(saved_history)} entries ---")

        # --- Second Request (with history expected) --- #
        request2 = LLMRequest(prompt=prompt2, session_id=session_id, model_name=model_name)
        
        # Patch the *instance* of the mock function to spy on its arguments
        # We use patch.object on the *specific instance* being used in this test
        print(f"--- Making second request for session {session_id} (expecting history) ---")
        with patch.object(mock_generate_func, '__call__', wraps=mock_generate_func.__call__) as mock_call:
            response2 = await handle_chat_request(request2, mock_generate_func, test_settings)
        
        assert response2.response == response2_expected

        # --- Assertions on Mock Call --- # 
        print("--- Asserting mock call arguments ---")
        # Check that the patched mock was called at least once (it should be exactly once here)
        mock_call.assert_called()

        # Get the arguments from the last call (should be the only call in the 'with' block)
        last_call_args, last_call_kwargs = mock_call.call_args
        
        # Check positional arguments (request object)
        assert len(last_call_args) == 1
        assert last_call_args[0] == request2 
        
        # Check keyword arguments (history)
        assert 'history' in last_call_kwargs
        passed_history = last_call_kwargs['history']
        assert isinstance(passed_history, list)
        assert len(passed_history) == 1
        
        # Check the content of the passed history
        assert passed_history[0].session_id == session_id
        assert passed_history[0].user_message == prompt1 # History should contain the first interaction
        assert passed_history[0].llm_response == response1_expected
        print("--- Mock call received history as expected ---")

    finally:
        # Clean up history for the session
        clear_history(session_id)
        print(f"--- Cleaned up history for session {session_id} ---")

@pytest.mark.asyncio
async def test_handle_chat_stream_success(mock_stream_func: LLMStreamingFunction):
    """Test handle_chat_stream successfully yields chunks from the injected LLM function."""
    test_prompt = "Tell me a joke"
    expected_full_response = "Why don't scientists trust atoms? Because they make up everything! (Mock Joke)"
    request = LLMRequest(prompt=test_prompt, session_id="test_session_stream", model_name="test-stream-svc")

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
    request = LLMRequest(prompt=test_prompt, session_id="test_session_stream_nf", model_name="test-stream-svc-nf")

    chunks = []
    async for chunk in handle_chat_stream(request, mock_stream_func):
        assert isinstance(chunk, StreamingChunk)
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == DEFAULT_NOT_FOUND_RESPONSE

    # Add model_name to request
    assert request.model_name == "test-stream-svc-nf"

# Add more tests later for error handling within the service if needed 