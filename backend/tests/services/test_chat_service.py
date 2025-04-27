import pytest
import pytest_asyncio
from pathlib import Path
from uuid import UUID # Import UUID
from datetime import datetime # Import datetime
from unittest.mock import patch, call, MagicMock, AsyncMock # Added AsyncMock

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
from backend.app.core.types import LLMFunction, LLMStreamingFunction
from backend.app.services.chat_service import handle_chat_request, handle_chat_stream
from backend.app.core.config import Settings # Import Settings
from backend.tests.mocks.mock_llm import (
    create_mock_llm_generate_func,
    create_mock_llm_stream_func,
    DEFAULT_NOT_FOUND_RESPONSE
)
# Import history service functions for testing -> NO LONGER NEEDED for history test
# from backend.app.services.history_service import get_history, clear_history 
from backend.app.models.history import HistoryEntry # Still need the model

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
async def test_handle_chat_request_with_history(
    mock_generate_func: LLMFunction,
    test_settings: Settings
):
    """Test that handle_chat_request interacts correctly with history_crud mock."""
    session_id = "test_session_hist_mock"
    model_name = "test-hist-model"
    prompt1 = "Hello" # Exists in mock_qa_pairs.json
    response1_expected = "Mock Hi there! This is a predefined answer."
    prompt2 = "How are you?" # Exists in mock_qa_pairs.json
    response2_expected = "I'm fine, thank you."

    # Expected history entry after first call
    expected_entry1 = HistoryEntry(
        session_id=session_id, user_message=prompt1, llm_response=response1_expected
    )

    # Patch the CRUD functions used by the history_service
    with patch('backend.app.services.history_service.history_crud.get_history', new_callable=AsyncMock) as mock_crud_get, \
         patch('backend.app.services.history_service.history_crud.add_history_entry', new_callable=AsyncMock) as mock_crud_add, \
         patch('backend.app.services.history_service.history_crud.clear_session_history', new_callable=AsyncMock) as mock_crud_clear: # Also mock clear if needed

        # Configure mock return values
        # First time get_history is called (before 1st request), return empty
        # Second time (before 2nd request), return the first entry
        mock_crud_get.side_effect = [[], [expected_entry1]]

        # --- First Request --- #
        request1 = LLMRequest(prompt=prompt1, session_id=session_id, model_name=model_name)
        print(f"\n--- Making first request (mocked CRUD) for session {session_id} ---")
        response1 = await handle_chat_request(request1, mock_generate_func, test_settings)
        assert response1.response == response1_expected

        # Verify CRUD calls for first request
        # get_history should have been called once (returning [])
        mock_crud_get.assert_called_once_with(session_id=session_id)
        # add_history_entry should have been called once
        mock_crud_add.assert_called_once()
        # Check the arguments passed to add_history_entry (ignore redis_conn which isn't passed directly here)
        # We need to compare the HistoryEntry object carefully
        call_args, call_kwargs = mock_crud_add.call_args
        assert call_args[0] == session_id # First arg is session_id
        added_entry = call_args[1]
        assert isinstance(added_entry, HistoryEntry)
        assert added_entry.session_id == expected_entry1.session_id
        assert added_entry.user_message == expected_entry1.user_message
        assert added_entry.llm_response == expected_entry1.llm_response
        print(f"--- CRUD mocks called as expected after first request ---")

        # Reset call counts for the next stage, keep side_effect
        # mock_crud_get.reset_mock() # reset_mock clears side_effect, don't use
        # Instead, just check call_count for the next assertion
        get_call_count_before_2nd = mock_crud_get.call_count
        add_call_count_before_2nd = mock_crud_add.call_count

        # --- Second Request (with history expected) --- #
        request2 = LLMRequest(prompt=prompt2, session_id=session_id, model_name=model_name)
        mock_llm_wrapper = MagicMock(wraps=mock_generate_func)
        print(f"--- Making second request (mocked CRUD) for session {session_id} ---")
        response2 = await handle_chat_request(request2, mock_llm_wrapper, test_settings)
        assert response2.response == response2_expected

        # Verify get_history was called again (returning [expected_entry1])
        assert mock_crud_get.call_count == get_call_count_before_2nd + 1
        # Verify add_history_entry was called again
        assert mock_crud_add.call_count == add_call_count_before_2nd + 1

        # --- Assertions on Mock LLM Call --- #
        print("--- Asserting mock LLM call arguments ---")
        mock_llm_wrapper.assert_called_once()
        last_call_args, last_call_kwargs = mock_llm_wrapper.call_args
        assert len(last_call_args) == 1
        assert last_call_args[0] == request2
        assert 'history' in last_call_kwargs
        passed_history = last_call_kwargs['history']
        assert isinstance(passed_history, list)
        # Check the history PASSED to the LLM function
        # It should be a copy of what mock_crud_get returned the *second* time
        assert len(passed_history) == 1
        assert passed_history[0].session_id == expected_entry1.session_id
        assert passed_history[0].user_message == expected_entry1.user_message
        assert passed_history[0].llm_response == expected_entry1.llm_response
        print("--- Mock LLM call received history as expected ---")

    # No 'finally' block needed as we are not modifying a real shared state

@pytest.mark.asyncio
async def test_handle_chat_stream_success(mock_stream_func: LLMStreamingFunction):
    """Test handle_chat_stream successfully yields chunks from the injected LLM function."""
    # This test doesn't directly involve history saving/loading state,
    # but it now calls get_history. We need to mock it.
    session_id = "test_session_stream"
    with patch('backend.app.services.history_service.history_crud.get_history', new_callable=AsyncMock, return_value=[]) as mock_crud_get_stream_success:
        test_prompt = "Tell me a joke"
        expected_full_response = "Why don't scientists trust atoms? Because they make up everything! (Mock Joke)"
        request = LLMRequest(prompt=test_prompt, session_id=session_id, model_name="test-stream-svc")

        chunks = []
        # Call the service function, injecting the mock streaming LLM function
        async for chunk in handle_chat_stream(request, mock_stream_func):
            assert isinstance(chunk, StreamingChunk) # Should be strings
            chunks.append(chunk)

        reassembled_response = "".join(chunks)
        assert reassembled_response == expected_full_response
        mock_crud_get_stream_success.assert_called_once_with(session_id=session_id)

@pytest.mark.asyncio
async def test_handle_chat_stream_not_found(mock_stream_func: LLMStreamingFunction):
    """Test handle_chat_stream with a prompt not in the mock data."""
    # This test doesn't directly involve history saving/loading state,
    # but it now calls get_history. We need to mock it.
    session_id = "test_session_stream_nf"
    with patch('backend.app.services.history_service.history_crud.get_history', new_callable=AsyncMock, return_value=[]) as mock_crud_get_stream_nf:
        test_prompt = "Another prompt that surely does not exist"
        request = LLMRequest(prompt=test_prompt, session_id=session_id, model_name="test-stream-svc-nf")

        chunks = []
        async for chunk in handle_chat_stream(request, mock_stream_func):
            assert isinstance(chunk, StreamingChunk)
            chunks.append(chunk)

        reassembled_response = "".join(chunks)
        assert reassembled_response == DEFAULT_NOT_FOUND_RESPONSE
        mock_crud_get_stream_nf.assert_called_once_with(session_id=session_id)

    # Add model_name to request - THIS ASSERTION IS IN THE WRONG PLACE
    # assert request.model_name == "test-stream-svc-nf" # Move this earlier if needed

# Add more tests later for error handling within the service if needed 