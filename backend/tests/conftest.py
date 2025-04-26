import pytest
from typing import AsyncIterator # Import AsyncIterator
# Use TestClient for testing FastAPI apps directly
from fastapi.testclient import TestClient
# Import ASGITransport for direct ASGI testing with httpx
from httpx import AsyncClient, ASGITransport

from backend.app.main import app # Import the FastAPI app instance

# --- Fixtures for Testing the FastAPI App --- #

@pytest.fixture(scope="session")
def client_sync() -> TestClient:
    """Provides a synchronous TestClient instance for the FastAPI app."""
    # TestClient is synchronous by default, wraps httpx
    with TestClient(app) as c:
        yield c

# Change scope to "function" for simplicity with pytest-asyncio
@pytest.fixture(scope="function")
# Hint that the function returns an async iterator yielding AsyncClient
async def client() -> AsyncIterator[AsyncClient]:
    """Provides an asynchronous httpx client configured to run against the FastAPI app."""
    # Use httpx.AsyncClient with ASGITransport pointing to the app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
         yield c

# --- Basic Test (using the async client) --- #

@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    """Test the root endpoint using the async client."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the LLM App API!"}

# --- Basic Test (using the sync client, if needed) --- #

def test_read_root_sync(client_sync: TestClient):
    """Test the root endpoint using the sync client."""
    response = client_sync.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the LLM App API!"}

# We will add more specific test files in subdirectories like tests/api, tests/services, etc. 