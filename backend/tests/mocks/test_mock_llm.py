import pytest
import pytest_asyncio
import json
import os
from pathlib import Path
from backend.app.models.chat import LLMRequest
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
TMP_DIR = Path(__file__).parent.parent.parent / "tmp" # Assumes tmp is at project root

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

    request = LLMRequest(prompt=test_prompt)
    # Call the function returned by the fixture
    response = await mock_generate_func(request)

    assert response.response == expected_response
    assert response.model_name == "mock-qa-gen-v1" # Updated model name check
    assert response.finish_reason == "stop"

@pytest.mark.asyncio
async def test_mock_generate_response_not_found(mock_generate_func: LLMFunction):
    """Tests generate_response when the prompt is not found."""
    test_prompt = "This prompt does not exist"
    request = LLMRequest(prompt=test_prompt)
    # Call the function returned by the fixture
    response = await mock_generate_func(request)

    assert response.response == DEFAULT_NOT_FOUND_RESPONSE
    assert response.model_name == "mock-qa-gen-v1"

@pytest.mark.asyncio
async def test_mock_stream_response_found(mock_stream_func: LLMStreamingFunction, mock_qa_data: dict):
    """Tests stream_response yields correct chunks for a found prompt."""
    test_prompt = "Tell me a joke"
    expected_response = mock_qa_data[test_prompt.lower()]

    request = LLMRequest(prompt=test_prompt)
    chunks = []
    # Call the function returned by the fixture
    async for chunk in mock_stream_func(request):
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == expected_response

@pytest.mark.asyncio
async def test_mock_stream_response_not_found(mock_stream_func: LLMStreamingFunction):
    """Tests stream_response yields correct chunks for a not-found prompt."""
    test_prompt = "Another prompt that does not exist"
    request = LLMRequest(prompt=test_prompt)
    chunks = []
    # Call the function returned by the fixture
    async for chunk in mock_stream_func(request):
        chunks.append(chunk)

    reassembled_response = "".join(chunks)
    assert reassembled_response == DEFAULT_NOT_FOUND_RESPONSE

@pytest.mark.asyncio
async def test_mock_output_to_tmp_file(mock_generate_func: LLMFunction, mock_qa_data: dict):
    """Tests generating a response and writing its JSON to a tmp file (for verification)."""
    # Ensure tmp directory exists
    TMP_DIR.mkdir(exist_ok=True)
    output_file = TMP_DIR / "mock_llm_response.json"

    test_prompt = "What is the capital of France?"
    request = LLMRequest(prompt=test_prompt)
    # Call the function returned by the fixture
    response = await mock_generate_func(request)

    # Write the response model to JSON
    with open(output_file, 'w') as f:
        f.write(response.model_dump_json(indent=2))

    # Basic check: verify the file was created and is not empty
    assert output_file.is_file()
    assert output_file.stat().st_size > 0

    # Clean up the file after test
    # os.remove(output_file) # Optional: uncomment to remove file after test run 