import pytest
import pytest_asyncio
import json
import os
from pathlib import Path
from backend.app.models.chat import LLMRequest, LLMResponse
from backend.app.core.types import LLMFunction, LLMStreamingFunction
# Import factory functions and constant
from backend.tests.mocks.mock_llm import (
    create_mock_llm_generate_func,
    create_mock_llm_stream_func,
    DEFAULT_NOT_FOUND_RESPONSE
)

# Define the path to the fixtures directory relative to this test file
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
QA_FILE_PATH = FIXTURES_DIR / "mock_qa_pairs.json"
# Define the path for test JSON outputs from this module
TEST_OUTPUT_DIR = FIXTURES_DIR / "test_json_sessions" / "mock_tests"

@pytest.fixture(scope="session")
def mock_qa_data() -> dict:
    """Loads the mock Q&A data from the JSON fixture."""
    with open(QA_FILE_PATH, 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_generate_func() -> LLMFunction:
    """Provides an instance of the mock generate function."""
    # Use high speed for tests to minimize delay
    return create_mock_llm_generate_func(qa_file_path=QA_FILE_PATH, emulation_speed_cps=10000)

@pytest.fixture
def mock_stream_func() -> LLMStreamingFunction:
    """Provides an instance of the mock stream function."""
    # Use high speed for tests to minimize delay
    return create_mock_llm_stream_func(qa_file_path=QA_FILE_PATH, emulation_speed_cps=10000)

@pytest.mark.asyncio
async def test_mock_generate_response_found(mock_generate_func: LLMFunction, mock_qa_data: dict):
    """Tests generate_response when the prompt is found (case-insensitive)."""
    test_prompt = "Hello"
    expected_response = mock_qa_data[test_prompt.lower()]

    request = LLMRequest(prompt=test_prompt, model_name="test-model")
    response_dict = await mock_generate_func(request)

    assert isinstance(response_dict, dict)
    assert response_dict["response"] == expected_response
    assert response_dict["model_name"] == "mock-qa-gen-v1"
    assert response_dict["finish_reason"] == "stop"

@pytest.mark.asyncio
async def test_mock_generate_response_not_found(mock_generate_func: LLMFunction):
    """Tests generate_response when the prompt is not found."""
    test_prompt = "This prompt does not exist"
    request = LLMRequest(prompt=test_prompt, model_name="test-model-nf")
    response_dict = await mock_generate_func(request)

    assert isinstance(response_dict, dict)
    assert response_dict["response"] == DEFAULT_NOT_FOUND_RESPONSE
    assert response_dict["model_name"] == "mock-qa-gen-v1"
    assert response_dict.get("finish_reason") == "stop"

@pytest.mark.asyncio
async def test_mock_stream_response_found(mock_stream_func: LLMStreamingFunction, mock_qa_data: dict):
    """Tests stream_response yields correct chunks for a found prompt."""
    test_prompt = "Tell me a joke"
    expected_response = mock_qa_data[test_prompt.lower()]

    request = LLMRequest(prompt=test_prompt, model_name="test-stream-model")
    chunks = []
    async for chunk in mock_stream_func(request):
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == expected_response

@pytest.mark.asyncio
async def test_mock_stream_response_not_found(mock_stream_func: LLMStreamingFunction):
    """Tests stream_response yields correct chunks for a not-found prompt."""
    test_prompt = "Another prompt that does not exist"
    request = LLMRequest(prompt=test_prompt, model_name="test-stream-model-nf")
    chunks = []
    async for chunk in mock_stream_func(request):
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == DEFAULT_NOT_FOUND_RESPONSE

@pytest.mark.asyncio
async def test_mock_output_to_test_sessions_file(mock_generate_func: LLMFunction, mock_qa_data: dict):
    """Tests generating a response dict and writing it to the mock test sessions directory."""
    # Ensure test output directory exists
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = TEST_OUTPUT_DIR / "test_mock_llm_output.json"

    test_prompt = "What is the capital of France?"
    request = LLMRequest(prompt=test_prompt, model_name="test-file-model")
    response_dict = await mock_generate_func(request)

    # Write the dictionary to JSON
    with open(output_file, 'w') as f:
        json.dump(response_dict, f, indent=2) # Use json.dump for dict

    # Basic check: verify the file was created and is not empty
    assert output_file.is_file()
    assert output_file.stat().st_size > 0

    # Optional: Clean up the file after test
    # output_file.unlink() # More robust way to remove Path object 