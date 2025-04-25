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
*   **Database:** PostgreSQL
*   **Caching:** Redis
*   **Task Queuing:** FastAPI Background Tasks / Celery (with Redis or RabbitMQ as broker)
*   **Testing:** Pytest
*   **Containerization:** Docker, Docker Compose
*   **Monitoring:** Prometheus, Grafana
*   **CI/CD:** GitHub Actions
*   **Cloud Platform:** Google Cloud Platform (GCP) - Artifact Registry, Cloud Run/GKE

## Proposed Project Structure 📁

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app setup
│   │   ├── api/            # API Endpoints (routers)
│   │   ├── core/           # Config, core settings
│   │   ├── crud/           # Database interaction logic
│   │   ├── models/         # Pydantic models (request/response)
│   │   ├── schemas/        # Database schemas (e.g., SQLAlchemy models)
│   │   ├── services/       # Business logic, LLM interaction
│   │   └── utils/          # Helper functions
│   ├── tests/              # Pytest tests for the backend
│   ├── terminal_chat.py  # Direct service test (manual)
│   ├── app.py            # API client test (manual)
│   └── Dockerfile          # Note: Will need update for pyproject.toml build
├── pyproject.toml          # Project definition and dependencies
├── frontend/
│   ├── public/
│   ├── src/                # React components, styles, logic
│   ├── Dockerfile          # Frontend Docker image build instructions
│   └── package.json        # Frontend dependencies
├── infra/
│   └── monitoring/         # Prometheus & Grafana configs
├── .github/
│   └── workflows/          # GitHub Actions CI/CD pipelines
├── docker-compose.yml      # Docker Compose configuration for all services
├── README.md               # You are here!
└── .gitignore
```
*(This structure is starting to evolve!)*

## Getting Started 🚀

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/end-to-end-llm-app.git
    cd end-to-end-llm-app
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    # Ensure you have Python 3.11+
    python3.11 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install the backend package and test dependencies:**
    ```bash
    # Install in editable mode (-e) with optional [test] dependencies
    pip install -e '.[test]'
    ```
4.  **Create temporary directory (if needed by tests):**
    ```bash
    mkdir -p tmp/
    ```

## Running the API Client Terminal Chat (Manual Testing) 💬

An alternative interactive terminal script (`backend/app.py`) acts as an HTTP client to test the running FastAPI application endpoints.

1.  **Ensure the FastAPI server is running:**
    ```bash
    # In terminal 1:
    source .venv/bin/activate
    uvicorn backend.app.main:app --reload
    ```
    Once running, you can access the interactive API documentation (Swagger UI) in your browser at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

2.  **Ensure Ollama is running** and accessible by the FastAPI server.
3.  **Run the client script in a separate terminal:**
    ```bash
    # In terminal 2:
    source .venv/bin/activate
    python backend/app.py
    ```
4.  Type your prompts and press Enter. Type `quit` or `exit` to end.

## Running the Direct Terminal Chat (Manual Testing) 🧑‍💻

A simple interactive terminal chat script (`backend/terminal_chat.py`) is provided for manually testing the connection and streaming with a running Ollama instance.

1.  **Ensure Ollama is running** and accessible (e.g., `ollama serve` or via Docker).
2.  **Ensure the required model is pulled** (e.g., `ollama pull deepseek-r1:14b`).
3.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
4.  **Run the script from the project root *as a module*:**
    ```bash
    python -m backend.terminal_chat
    ```
5.  Type your prompts and press Enter. Type `quit` or `exit` to end.

## Running Tests ✅

This project uses `pytest` for testing. Ensure you have installed the project with test dependencies (`pip install -e '.[test]'`).

Run tests from the project root directory. **It is recommended to run `pytest` using the virtual environment's Python interpreter** to avoid path issues:
```bash
# Activate venv first if not already active
source .venv/bin/activate

# Recommended way to run pytest:
.venv/bin/python -m pytest
```

*   **Service Tests (`backend/tests/services/`):** Tests for the business logic layer.
    ```bash
    .venv/bin/python -m pytest backend/tests/services/
    ```

*   **API Tests (`backend/tests/api/`):** These tests use FastAPI's dependency overriding feature. They replace the actual Ollama client functions with mock versions defined in `backend/tests/mocks/mock_llm.py` which use predefined question/answer pairs from `backend/tests/fixtures/mock_qa_pairs.json`. This isolates the API layer for testing.
    ```bash
    .venv/bin/python -m pytest backend/tests/api/
    # Or a specific file:
    # .venv/bin/python -m pytest backend/tests/api/test_chat_api.py
    ```

*   **Mock/Utility Tests (`backend/tests/mocks/`, `backend/tests/utils/`):** Tests for helper functions and mocking utilities.
    ```bash
    .venv/bin/python -m pytest backend/tests/mocks/
    ```

*   **Run tests in a specific file (e.g., mock tests):**
    ```bash
    .venv/bin/python -m pytest backend/tests/mocks/test_mock_llm.py
    ```

*   **Run a specific test function by name:**
    Use the `-k` flag followed by a string expression that matches part of the test function name.
    ```bash
    # Example: Run only the test_mock_generate_response_found test
    .venv/bin/python -m pytest backend/tests/mocks/test_mock_llm.py -k test_mock_generate_response_found
    ```

*   **See output (`print` statements) and more details:**
    Use the `-s` (capture disabled) and `-v` (verbose) flags.
    ```bash
    .venv/bin/python -m pytest -s -v
    ```

Let's build something awesome and learn a ton along the way!

