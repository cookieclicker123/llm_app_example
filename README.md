# End-to-End LLM App: Mastering the Stack

This project is a hands-on exercise in building a complete, production-ready application centered around a Large Language Model (LLM). While the core LLM functionality (a finance-focused chatbot) is kept simple, the primary goal is to implement and master the tools, techniques, and best practices required for developing, deploying, monitoring, and scaling modern AI-powered applications.

## Core Philosophy ✨

*   **Learning & Process over Complexity:** Focus on the *how* (robust engineering, efficient workflows) rather than just the *what* (complex AI features).
*   **Test-Driven Development (TDD):** Write tests first! Ensure code quality, maintainability, and confidence using `pytest`.
*   **Stateless & Modular Design:** Build reusable, pure functions and clearly separated modules (data access, utilities, external service interactions) for a clean and scalable backend.
*   **Asynchronous First:** Leverage `asyncio` and `FastAPI` for high-performance, non-blocking I/O, essential for responsive LLM interactions.
*   **Infrastructure as Code:** Define and manage infrastructure reliably using Docker and Docker Compose.
*   **Continuous Integration & Deployment (CI/CD):** Automate testing, linting, building, and deployment using GitHub Actions for faster feedback loops and safer releases.
*   **Observability:** Integrate monitoring (Prometheus) and visualization (Grafana) from the start to understand application health and performance.

## Technology Stack 🛠️

*   **Backend:** Python, FastAPI, asyncio
*   **LLM Serving:** Ollama (for local development/testing)
*   **Frontend:** React, TypeScript (potentially)
*   **Database:** PostgreSQL (Future)
*   **Caching & History:** Redis (Currently used for persistent chat history)
*   **Task Queuing:** FastAPI Background Tasks / Celery (Future)
*   **Testing:** Pytest
*   **Containerization:** Docker, Docker Compose
*   **Monitoring:** Prometheus, Grafana (Future)
*   **CI/CD:** GitHub Actions (Future)
*   **Cloud Platform:** Google Cloud Platform (GCP) - Artifact Registry, Cloud Run/GKE (Future)

## Proposed Project Structure 📁

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app setup, lifespan events
│   │   ├── api/            # API Endpoints (routers)
│   │   ├── core/           # Config, core settings, dependencies
│   │   ├── crud/           # Database/Redis interaction logic
│   │   ├── models/         # Pydantic models (request/response)
│   │   ├── schemas/        # Database schemas (e.g., SQLAlchemy models)
│   │   ├── services/       # Business logic, LLM interaction, history management
│   │   └── utils/          # Helper functions, external clients (e.g., Ollama)
│   ├── tests/              # Pytest tests for the backend
│   ├── app.py            # Terminal API client (with session handling)
│   └── Dockerfile
├── pyproject.toml          # Project definition and dependencies
├── frontend/               # (Placeholder for future frontend)
│   └── ...
├── infra/                  # (Placeholder for future monitoring/infra configs)
│   └── ...
├── .github/                # (Placeholder for future CI/CD workflows)
│   └── ...
├── docker-compose.yml      # Docker Compose configuration for all services
├── pytest.ini              # Pytest configuration (e.g., warning filters)
├── README.md               # You are here!
└── .gitignore
```

## Getting Started 🚀

1.  **Prerequisites:**
    *   Docker & Docker Compose
    *   Python 3.11+
    *   Ollama installed and running locally (see [Ollama website](https://ollama.com/))
    *   Pull an Ollama model (e.g., `ollama pull gemma3:12b-it-qat`) - the default model is set in `backend/app/core/config.py`.

2.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd end-to-end-llm-app
    ```
3.  **(Optional) Create and activate a virtual environment:**
    While dependencies are installed in the Docker image, you might want a local venv for IDE integration or direct script running.
    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -e '.[test]' # Installs backend + test deps locally
    ```
4.  **Build and start services:**
    This will build the backend image and start both the backend and Redis containers.
    ```bash
    docker compose up --build -d
    ```
    *   `-d` runs containers in detached mode.
    *   `--build` forces a rebuild of images if their source (Dockerfile, code) has changed.

5.  **Check container status:**
    ```bash
    docker ps
    ```
    You should see `end_to_end_llm_app-backend-1` and `end_to_end_llm_app-redis-1` running.

6.  **Check API:** Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to see the FastAPI documentation.

## Using the Application

### Interactive Terminal Client

The easiest way to interact with the API and test session persistence.

1.  **Ensure services are running** (`docker compose up -d`).
2.  **Run the client:**
    ```bash
    python backend/app.py
    ```
3.  **Session Handling:** The client will connect to Redis and prompt you:
    *   It lists existing session IDs found in Redis.
    *   Enter `0` to start a new session with a random ID.
    *   Enter the index number corresponding to an existing session ID to resume it.
4.  Chat with the LLM. Type `quit` or `exit` to end.

### Using `curl`

You can also interact directly with the API endpoints using `curl`.

*   **Required Headers:** `-H "Content-Type: application/json"`
*   **Required Body Fields:** `prompt` (string), `session_id` (string), `model_name` (string)

**Example: Non-Streaming Chat (`/api/v1/chat/`)**

```bash
SESSION_ID="my_curl_session_1"
MODEL_NAME="gemma3:12b-it-qat" # Or your preferred model

# First request
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d "{\
        \"prompt\": \"What is the capital of France?",\
        \"session_id\": \"$SESSION_ID\",\
        \"model_name\": \"$MODEL_NAME\"\
      }"

# Second request (same session)
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d "{\
        \"prompt\": \"How many people live there?",\
        \"session_id\": \"$SESSION_ID\",\
        \"model_name\": \"$MODEL_NAME\"\
      }"
```
*Note: The non-streaming endpoint returns the full `LLMResponse` object as JSON.* 

**Example: Streaming Chat (`/api/v1/chat/stream`)**

```bash
SESSION_ID="my_curl_session_2"
MODEL_NAME="gemma3:12b-it-qat"

curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\
        \"prompt\": \"Tell me about Redis.",\
        \"session_id\": \"$SESSION_ID\",\
        \"model_name\": \"$MODEL_NAME\"\
      }" \
  --no-buffer
```
*Note: `--no-buffer` is recommended with `curl` for streaming to see chunks as they arrive. The streaming endpoint returns plain text chunks.* 

## Development Workflow

### Redis Persistence

*   Chat history is now stored in the `redis` service container using Redis Lists.
*   Each session ID maps to a key in Redis (prefixed with `session:`).
*   Each key holds a list where each element is a JSON string representing a `HistoryEntry` (user message + LLM response).
*   Data persists as long as the Redis volume (`redis_data`) exists. Stopping and starting containers with `docker compose up`/`down`/`stop`/`start` will preserve history.
*   **Stopping only the backend:** If you want to restart the backend *without* losing the current session history (useful during development), use:
    ```bash
    docker compose stop backend
    # Make code changes
    docker compose build backend # Rebuild if needed
    docker compose up -d backend # Restart backend, Redis was untouched
    ```

### Forcing Rebuild without Cache (`--no-cache`)

Sometimes Docker's build cache can cause issues if it reuses old layers when you need fresh code or dependencies.

*   **Normal build:** `docker compose build backend` (Uses cache, faster for minor code changes).
*   **Build without cache:** `docker compose build --no-cache backend`
    *   **Use cases:**
        *   After significant code changes, especially if you suspect caching issues.
        *   After changing dependencies in `pyproject.toml` if the `pip install` layer wasn't invalidated.
        *   After changing base images or earlier steps in the `Dockerfile`.
        *   When troubleshooting unexpected behavior that might stem from stale code in the image.

### Inspecting Redis Data

You can directly view the history stored in Redis:

1.  **Connect to Redis:**
    ```bash
    docker compose exec redis redis-cli
    ```
2.  **Useful Commands inside `redis-cli`:**
    *   `PING`: Should return `PONG`.
    *   `KEYS "session:*"`: List all keys used for session history.
    *   `TYPE session:<session_id>`: Should return `list`.
    *   `LLEN session:<session_id>`: Show how many turns are in the history list.
    *   `LRANGE session:<session_id> 0 -1`: Show all history entries (JSON strings) for the session (newest at the top/index 0).
    *   `LINDEX session:<session_id> 0`: Show the most recent history entry (JSON string).
    *   `DEL session:<session_id>`: Delete the history for a specific session.
    *   `FLUSHDB`: **DANGER!** Deletes *all* keys in the current database (DB 0 by default).
    *   `exit`: Quit `redis-cli`.

## Running Tests ✅

This project uses `pytest` for testing. Ensure you have installed the project with test dependencies (`pip install -e '.[test]'`).

Tests can be run locally (if venv is set up) or inside the Docker container.

**Running Tests Inside Docker (Recommended):**

This ensures tests run in the same environment as the application.

1.  Make sure containers are running: `docker compose up -d`
2.  Execute pytest within the backend container:
    ```bash
    docker compose exec backend python -m pytest
    ```
    *   Add flags like `-v` (verbose) or `-k test_my_function` as needed.
    *   The `pytest.ini` file filters out common noisy warnings.

**Running Tests Locally:**

Requires installing dependencies locally (`pip install -e '.[test]'`).
```bash
# Activate venv first
source .venv/bin/activate

# Run pytest
python -m pytest
```

*(See previous README section for more detailed pytest commands if needed)*

Let's build something awesome and learn a ton along the way!

