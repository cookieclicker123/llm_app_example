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
│   ├── Dockerfile          # Backend Docker image build instructions
│   └── requirements.txt    # Backend Python dependencies
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
*(This structure is a starting point and will evolve.)*

## Getting Started 🚀

*(Instructions to be added here - cloning, environment setup, running `docker-compose up`)*

Let's build something awesome and learn a ton along the way!
