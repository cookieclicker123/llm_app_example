# Docker Setup for End-to-End LLM App

This document explains how to build and run the application using Docker and Docker Compose.

## Overview

We use Docker to containerize the application components, ensuring consistent environments and simplifying setup and deployment.

*   **`backend/Dockerfile`**: Defines how to build the Docker image for the FastAPI backend service. It includes installing Python, dependencies from `pyproject.toml`, copying the application code, and setting the command to run the `uvicorn` server.
*   **`docker-compose.yml`**: Defines the services that make up the application stack. It orchestrates the `backend`, `postgres` (PostgreSQL database), and `redis` (cache/history) services, along with their networking and volumes.
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
2.  **Edit the `.env` file:** Open the `.env` file and fill in values. Key variables include:
    *   `OPENAI_API_KEY`
    *   `POSTGRES_DB`, `POSTGRES_USER`: Database name and user (must match `docker-compose.yml`).
    *   `POSTGRES_PASSWORD`: **Generate a secure password** for the database user.
    *   `DATABASE_URL`: The full connection string used by SQLAlchemy. The default `postgresql+asyncpg://<user>:<password>@postgres:5432/<db>` uses the service name `postgres` and should work correctly *inside* the Docker network.
    *   `REDIS_URL`: The connection string for Redis (e.g., `redis://redis:6379/0`). Include password if Redis is configured with one.
    *   `JWT_SECRET_KEY`: **Generate a strong secret key** (e.g., `openssl rand -hex 32`) for signing authentication tokens.
    *   `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Defaults usually suffice.
    *   `OLLAMA_BASE_URL`: If Ollama runs on host, likely `http://host.docker.internal:11434`.

    *   **Note on `DATABASE_URL` for local Alembic:** If you run `alembic` commands directly on your host machine (outside Docker), you'll need to temporarily change the hostname in `DATABASE_URL` within your `.env` file from `postgres` to `localhost` (or `127.0.0.1`) so Alembic can connect to the port exposed by the Docker container.

**Remember:** The `.env` file should **not** be committed to version control (it's listed in `.gitignore` and `.dockerignore`).

## Building Images

To build the Docker images for all services defined in `docker-compose.yml` (currently just `backend`, as `postgres` and `redis` use pre-built images):

```bash
docker compose build
# Or specifically: docker compose build backend
```

## Running the Application Stack

1.  **Start all services:**
    ```bash
    # Run detached (in background)
    docker compose up -d
    
    # To force rebuild images before starting:
    docker compose up --build -d 
    ```
    Docker Compose will start `redis`, then `postgres` (and wait for its healthcheck), and finally the `backend` service, respecting the `depends_on` configuration.

2.  **Check Logs:** Verify services started correctly.
    ```bash
    docker compose logs -f backend
    docker compose logs postgres
    docker compose logs redis
    ```

3.  **Apply Database Migrations:** The first time you start the stack, or after adding new database models, you need to apply the Alembic migrations to create/update tables in the PostgreSQL container.
    ```bash
    # Run inside the backend container (recommended)
    docker compose exec backend alembic upgrade head
    
    # Or run from host (requires DATABASE_URL in .env pointing to localhost:5432)
    # alembic -c backend/alembic.ini upgrade head
    ```

## Accessing and Testing the Running Application

Once all containers are running and migrations are applied:

*   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs). Explore API endpoints, including `/auth` and `/sessions`.
*   **Health Check (Root):** `curl http://localhost:8000/`

*   **Testing Endpoints with `curl`:** (See `README.md` for detailed examples including authentication token retrieval and usage).

*   **Running the Terminal Client (`app.py`):** (Currently outdated, needs updates for authentication - see `README.md`).

*   **Connecting to PostgreSQL Container:**
    ```bash
    docker compose exec postgres psql -U appuser -d appdb
    # Enter password from .env when prompted
    # Use psql commands like \dt, SELECT * FROM users;, \q
    ```

*   **Connecting to Redis Container:**
    ```bash
    docker compose exec redis redis-cli
    # Use redis commands like KEYS "session:*", LRANGE session:<uuid> 0 -1, exit
    ```

*   **Running Tests Inside the Container:**
    ```bash
    docker compose exec backend python -m pytest
    # Add flags as needed, e.g., -v
    ```
    Ensure tests run against the containerized environment.

## Stopping the Application Stack

```bash
# Stop and remove containers, networks, volumes defined in docker-compose.yml
docker compose down

# To remove volumes (like postgres_data, redis_data - THIS DELETES DATA):
docker compose down -v

# If you only want to stop without removing:
docker compose stop
```