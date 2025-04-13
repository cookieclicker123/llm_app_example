import pytest
from httpx import AsyncClient

from backend.app.main import app # Adjust the import path as necessary

# This fixture provides an asynchronous test client for making requests to the FastAPI app.
# It ensures the app runs in a test mode.
@pytest.fixture(scope="session")
async def client():
    # Using AsyncClient from httpx for async FastAPI testing
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

# Example basic test
@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the LLM App API!"}

# We will add more specific test files in subdirectories like tests/api, tests/services, etc. 