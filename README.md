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

*   **Backend:** Python, FastAPI, asyncio, SQLAlchemy, Alembic, Passlib, python-jose
*   **LLM Serving:** Ollama (for local development/testing)
*   **Frontend:** React, TypeScript (potentially)
*   **Database:** PostgreSQL (User accounts, Session Metadata)
*   **Caching & History:** Redis (Chat history content)
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
│   │   ├── api/            # API Endpoints (routers: chat, auth, sessions)
│   │   ├── core/           # Config, core settings, dependencies, security
│   │   ├── crud/           # Database/Redis interaction logic (user, session, history)
│   │   ├── db/             # DB Session setup, Base class
│   │   ├── models/         # SQLAlchemy models (User, ConversationSession)
│   │   ├── schemas/        # Pydantic schemas (request/response/db mapping)
│   │   ├── services/       # Business logic, LLM interaction, history management
│   │   └── utils/          # Helper functions, external clients (e.g., Ollama)
│   ├── tests/              # Pytest tests for the backend
│   ├── alembic/            # Alembic migration scripts
│   ├── alembic.ini         # Alembic configuration
│   ├── app.py            # DEPRECATED/NEEDS UPDATE: Terminal API client
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
    cd end_to_end_llm_app
    ```
3.  **Configure Environment:**
    *   Copy `.env.example` to `.env`: `cp .env.example .env`
    *   Edit `.env` and fill in values for:
        *   `OPENAI_API_KEY` (if needed later)
        *   `POSTGRES_PASSWORD` (generate a secure password)
        *   `JWT_SECRET_KEY` (generate using `openssl rand -hex 32`)
        *   Verify `DATABASE_URL` and `REDIS_URL` match your setup (defaults should work with Docker Compose).
    *   **Important:** Do NOT commit `.env` to Git.

4.  **(Optional) Create and activate a virtual environment:**
    While dependencies are installed in the Docker image, you might want a local venv for IDE integration or direct script running.
    ```bash
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -e '.[test]' # Installs backend + test deps locally
    ```
5.  **Build and start services:**
    This will build the backend image and start the `backend`, `postgres`, and `redis` containers.
    ```bash
    docker compose up --build -d
    ```
    *   `-d` runs containers in detached mode.
    *   `--build` forces a rebuild of images if their source (Dockerfile, code) has changed.

6.  **Apply Database Migrations:**
    Run the Alembic migrations to create the necessary tables in the PostgreSQL database.
    ```bash
    # Run from project root
    alembic -c backend/alembic.ini upgrade head
    # Alternatively, run inside the backend container:
    # docker compose exec backend alembic upgrade head
    ```
    *   Note: You might need to adjust `DATABASE_URL` in `.env` to use `localhost` instead of `postgres` when running Alembic commands directly from your host, as explained in DOCKER.md.

7.  **Check container status:**
    ```bash
    docker ps
    ```
    You should see `backend`, `postgres`, and `redis` containers running.

8.  **Check API:** Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser. You should see the API documentation, including new endpoints for `/auth` and `/sessions`.

## Using the Application

### Interactive Terminal Client (Needs Update)

**NOTE:** The current `backend/app.py` terminal client is **outdated** and does **not** support the new authentication flow. It needs to be updated to:
1.  Prompt for username and password.
2.  Call the `/api/v1/auth/token` endpoint to get a JWT.
3.  Use the obtained token in an `Authorization: Bearer <token>` header for subsequent requests.
4.  Call the `/api/v1/sessions/` endpoint to list sessions.
5.  Allow selecting an existing session or starting a new one.
6.  Send the `session_id` (which is a UUID) and the token to the chat endpoints.

*(This update is left as a future exercise for now.)*

### Using `curl`

You can interact with the API using `curl`. You first need to obtain an access token.

1.  **Register a User (Endpoint TBD):** (Currently, no registration endpoint exists. You might need to create a user directly in the database for initial testing).

2.  **Get Access Token (`/api/v1/auth/token`):**
    Replace `testuser` and `testpassword` with the credentials of a user you created.
    ```bash
    # Use application/x-www-form-urlencoded for token endpoint
    ACCESS_TOKEN_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/auth/token \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=testuser&password=testpassword")
    
    # Extract the token (requires jq - install if needed: brew install jq)
    ACCESS_TOKEN=$(echo $ACCESS_TOKEN_RESPONSE | jq -r .access_token)
    
    echo "Access Token: $ACCESS_TOKEN"
    ```

3.  **List Sessions (`/api/v1/sessions/`):**
    Use the obtained token in the Authorization header.
    ```bash
    curl -X GET http://localhost:8000/api/v1/sessions/ \
      -H "Authorization: Bearer $ACCESS_TOKEN"
    ```
    *This will return a list of session metadata JSON objects.* 

4.  **Start/Continue Chat (Non-Streaming - `/api/v1/chat/`):**
    Choose a `session_id` (UUID string) - either from the list above or generate a new one (e.g., using `uuidgen` or Python's `uuid.uuid4()`).
    ```bash
    SESSION_ID="$(uuidgen)" # Example: Generate a new UUID for a new session
    # Or use an existing session_uuid from the list command
    MODEL_NAME="gemma3:12b-it-qat" # Or your preferred model

    curl -X POST http://localhost:8000/api/v1/chat/ \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d "{\
            \"prompt\": \"What is the capital of France?",\
            \"session_id\": \"$SESSION_ID\",\
            \"model_name\": \"$MODEL_NAME\"\
          }"
    ```

5.  **Start/Continue Chat (Streaming - `/api/v1/chat/stream`):**
    ```bash
    SESSION_ID="$(uuidgen)" # Or use an existing one
    MODEL_NAME="gemma3:12b-it-qat"

    curl -X POST http://localhost:8000/api/v1/chat/stream \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d "{\
            \"prompt\": \"Tell me about Redis.",\
            \"session_id\": \"$SESSION_ID\",\
            \"model_name\": \"$MODEL_NAME\"\
          }" \
      --no-buffer
    ```

## Development Workflow

### Data Persistence
*   **User Accounts & Session Metadata:** Stored in the `postgres` service container using PostgreSQL. Data persists as long as the PostgreSQL volume (`postgres_data`) exists.
*   **Chat History Content:** Stored in the `redis` service container using Redis Lists. Data persists as long as the Redis volume (`redis_data`) exists.

### Stopping Only the Backend:
If you want to restart the backend *without* losing the current session history (useful during development), use:
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

You can directly view the *chat history* stored in Redis:

1.  **Connect to Redis:**
    ```bash
    docker compose exec redis redis-cli
    ```
2.  **Useful Commands inside `redis-cli`:**
    *   `PING`: Should return `PONG`.
    *   `KEYS "session:*"`: List all keys used for session history.
    *   `TYPE session:<session_id>`: Should return `list`.
    *   `LLEN session:<session_id>`: Show how many turns are in the history list.
    *   `LRANGE session:<session_id> 0 -1`: Show all history entries (JSON strings) for the session.
    *   `DEL session:<session_id>`: Delete the history for a specific session.
    *   `FLUSHDB`: **DANGER!** Deletes *all* keys in the current database (DB 0 by default).
    *   `exit`: Quit `redis-cli`.

### Inspecting PostgreSQL Data

You can connect to the PostgreSQL database running in Docker to inspect user accounts and session metadata.

1.  **Connect using `psql`:**
    ```bash
    docker compose exec postgres psql -U appuser -d appdb
    # You will be prompted for the password defined in your .env file
    ```
2.  **Useful `psql` Commands:**
    *   `\dt`: List all tables (should show `users`, `conversation_sessions`, `alembic_version`).
    *   `\d users`: Describe the users table columns.
    *   `\d conversation_sessions`: Describe the sessions table.
    *   `SELECT * FROM users;`: Show all users.
    *   `SELECT * FROM conversation_sessions WHERE user_id = '<user-uuid>';`: Show sessions for a specific user.
    *   `\q`: Quit `psql`.

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
    *   Note: Database-dependent tests might require additional setup (e.g., a separate test database, fixtures to manage data).

**Running Tests Locally:**

Requires installing dependencies locally (`pip install -e '.[test]'`).
```bash
# Activate venv first
source .venv/bin/activate

# Run pytest
python -m pytest
```

Let's build something awesome and learn a ton along the way!