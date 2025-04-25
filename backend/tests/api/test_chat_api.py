import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from pathlib import Path

from httpx import AsyncClient

from backend.app.models.chat import LLMRequest, LLMResponse, StreamingChunk
# Import the main app instance to override dependencies
from backend.app.main import app
# Import the dependency provider functions we want to override
from backend.app.api.chat import get_ollama_generate, get_ollama_stream
# Import our mock factories
from backend.tests.mocks.mock_llm import (
    create_mock_llm_generate_func,
    create_mock_llm_stream_func,
    DEFAULT_NOT_FOUND_RESPONSE
)

# --- Test Setup: Dependency Overrides --- #

# Define the path to the mock QA data
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
QA_FILE_PATH = FIXTURES_DIR / "mock_qa_pairs.json"

# Create instances of our MOCK LLM functions
mock_generate = create_mock_llm_generate_func(QA_FILE_PATH)
mock_stream = create_mock_llm_stream_func(QA_FILE_PATH)

# Define functions that return our mocks (to be used in overrides)
def override_get_ollama_generate():
    return mock_generate

def override_get_ollama_stream():
    return mock_stream

# Apply the overrides to the FastAPI app instance for this test module
app.dependency_overrides[get_ollama_generate] = override_get_ollama_generate
app.dependency_overrides[get_ollama_stream] = override_get_ollama_stream

# --- Test Cases --- #

@pytest.mark.asyncio
async def test_chat_endpoint_success(client: AsyncClient): # No mock patching needed now
    """Test successful non-streaming chat request using dependency override."""
    request_data = {"prompt": "Hello", "session_id": "api_test_gen_dep"}

    response = await client.post("/api/v1/chat/", json=request_data)

    assert response.status_code == 200
    response_json = response.json()
    # Check against the expected response from mock_qa_pairs.json
    assert response_json["response"] == "Mock Hi there! This is a predefined answer."
    assert response_json["model_name"] == "mock-qa-gen-v1"
    assert "created_at" in response_json
    assert "api_test_gen_dep" in response_json["request_id"]

@pytest.mark.asyncio
async def test_chat_stream_endpoint_success(client: AsyncClient): # No mock patching needed now
    """Test successful streaming chat request using dependency override."""
    expected_full_response = "Why don't scientists trust atoms? Because they make up everything! (Mock Joke)"
    request_data = {"prompt": "Tell me a joke", "session_id": "api_test_stream_dep"}

    response = await client.post("/api/v1/chat/stream", json=request_data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    streamed_text = await response.aread()
    assert streamed_text.decode() == expected_full_response

@pytest.mark.asyncio
async def test_chat_endpoint_not_found(client: AsyncClient):
    """Test non-streaming endpoint with a prompt not in mock data."""
    request_data = {"prompt": "Does not exist", "session_id": "api_test_gen_nf"}
    response = await client.post("/api/v1/chat/", json=request_data)
    assert response.status_code == 200
    assert response.json()["response"] == DEFAULT_NOT_FOUND_RESPONSE

@pytest.mark.asyncio
async def test_chat_stream_endpoint_not_found(client: AsyncClient):
    """Test streaming endpoint with a prompt not in mock data."""
    request_data = {"prompt": "Also does not exist", "session_id": "api_test_stream_nf"}
    response = await client.post("/api/v1/chat/stream", json=request_data)
    assert response.status_code == 200
    streamed_text = await response.aread()
    assert streamed_text.decode() == DEFAULT_NOT_FOUND_RESPONSE

# Clean up overrides after tests in this module are done (optional but good practice)
@pytest.fixture(scope="module", autouse=True)
def cleanup_dependency_overrides():
    yield
    app.dependency_overrides = {}

# Error handling tests can be added similarly, potentially by creating
# mock functions that raise exceptions and overriding dependencies with those. 