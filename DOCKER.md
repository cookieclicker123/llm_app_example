# Docker Setup for End-to-End LLM App

This document explains how to build and run the application using Docker and Docker Compose.

## Overview

We use Docker to containerize the application components, ensuring consistent environments and simplifying setup and deployment.

*   **`backend/Dockerfile`**: Defines how to build the Docker image for the FastAPI backend service. It includes installing Python, dependencies from `pyproject.toml`, copying the application code, and setting the command to run the `uvicorn` server.
*   **`docker-compose.yml`**: Defines the services that make up the application stack. Initially, it defines only the `backend` service. Later, it will orchestrate the `backend`, a PostgreSQL database (`db`), a Redis cache (`redis`), and potentially the Ollama server (`ollama`) itself.
*   **`.dockerignore`**: Specifies files and directories that should be excluded from the Docker build context to keep images small and builds fast.
*   **`.env.example`**: A template file showing the environment variables used for configuration. Copy this to `.env` for local setup.
*   **`.env`**: (You create this file, **do not commit to Git**) Contains your actual local configuration values (like API keys, database URLs, Ollama URL). Docker Compose automatically loads variables from this file.

## Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) installed and running.
*   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop).

## Environment Configuration (`.env` file)

Before running the application with Docker Compose, you need to configure the necessary environment variables.

1.  **Copy the example file:**
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file:** Open the newly created `.env` file and adjust the values as needed for your local setup. 
    *   **Crucially**, if Ollama is running directly on your host machine (not in Docker), you likely need to change `OLLAMA_BASE_URL` to `http://host.docker.internal:11434` so the backend container can reach it.
    *   Fill in database URLs, Redis URLs, secrets, etc., as those features are implemented.

**Remember:** The `.env` file should **not** be committed to version control (it's listed in `.gitignore` and `.dockerignore`).

## Building the Backend Image

To build the Docker image for the backend service defined in `docker-compose.yml`:

```bash
docker compose build backend
# Or simply `docker-compose build` if it's the only service defined
```

This command reads `docker-compose.yml`, finds the `backend` service, looks at its `build` instructions (context `./backend`, file `Dockerfile`), and executes the steps in `backend/Dockerfile` to create an image.

## Running the Backend Service

1.  **Start the service:**
    ```bash
    # Run in foreground (logs to terminal, press Ctrl+C to stop)
    docker compose up backend

    # Or run detached (in background)
    docker compose up -d backend
    ```

2.  **Check Logs (especially if running detached):** Verify that Uvicorn started correctly.
    ```bash
    docker compose logs backend
    # Look for lines like "Uvicorn running on http://0.0.0.0:8000"
    # Use `docker compose logs -f backend` to follow logs live.
    ```

**Important:** For the application inside the container to connect to Ollama, Ollama needs to be running and accessible *from the container*. See the Environment Configuration section above for details on setting `OLLAMA_BASE_URL` in your `.env` file correctly depending on how Ollama is run.

## Accessing and Testing the Running Application

Once the `backend` container is running:

*   **Swagger UI:** Open your web browser and navigate to [http://localhost:8000/docs](http://localhost:8000/docs). You can explore and interact with the API endpoints here.

*   **Health Check (Root):** Open [http://localhost:8000/](http://localhost:8000/) in your browser or use curl:
    ```bash
    curl http://localhost:8000/
    ```

*   **Testing Endpoints with `curl`:** Send requests directly from your host terminal:

    *   **Non-streaming (`/api/v1/chat/`):**
        ```bash
        curl -X POST http://localhost:8000/api/v1/chat/ \
          -H "Content-Type: application/json" \
          -d '{
                "prompt": "Hello",
                "session_id": "curl_test_1",
                "model_name": "gemma3:12b-it-qat"
              }'
        ```

    *   **Streaming (`/api/v1/chat/stream`):**
        ```bash
        curl -X POST http://localhost:8000/api/v1/chat/stream \
          -H "Content-Type: application/json" \
          -d '{
                "prompt": "Tell me a joke",
                "session_id": "curl_test_2",
                "model_name": "gemma3:12b-it-qat"
              }' --no-buffer
        # --no-buffer is helpful to see stream output immediately
        ```

*   **Running the Terminal Client (`app.py`):** Run the interactive client from your host machine (ensure your virtual environment is active):
    ```bash
    source .venv/bin/activate
    python backend/app.py
    ```
    This script connects to `http://127.0.0.1:8000`, which is mapped to the container's port.

*   **Running Tests Inside the Container:** Execute `pytest` within the container's environment. It's recommended to explicitly set the `asyncio` mode to `auto` to avoid potential issues with async fixtures in some environments:
    ```bash
    # Run all tests (recommended mode)
    docker compose exec backend python -m pytest --asyncio-mode=auto

    # Run tests in a specific directory (e.g., API tests)
    docker compose exec backend python -m pytest --asyncio-mode=auto backend/tests/api/

    # Run a specific test file
    docker compose exec backend python -m pytest --asyncio-mode=auto backend/tests/api/test_chat_api.py
    ```
    This ensures the tests run with the exact dependencies and environment defined in the `Dockerfile`.

## Stopping the Service

```bash
# Stop and remove containers, networks defined in docker-compose.yml
docker compose down

# If you only want to stop without removing:
docker compose stop backend
```