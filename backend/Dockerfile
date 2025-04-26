# Stage 1: Build environment with dependencies
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build tools
RUN pip install --upgrade pip
RUN pip install build # Needed to build the package from pyproject.toml

# Copy project definition (from project root context)
COPY pyproject.toml ./ 
# COPY poetry.lock* pyproject.toml ./ # If using poetry

# Copy the backend source code FIRST
# Note: .dockerignore should prevent copying .venv etc.
COPY ./backend /app/backend

# Now install dependencies, which will also install the local package
RUN pip install ".[test]" # Install with test dependencies for running tests later

# (Optional) Run tests within the build stage to fail early
# RUN .venv/bin/python -m pytest 

# Stage 2: Final runtime environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user and group
RUN addgroup --system app && adduser --system --ingroup app app

# Copy installed dependencies (libraries AND executables) from the builder stage
# Ensure destination paths end with / for clarity when copying directories
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
# Copy executables (like uvicorn)
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code from the builder stage
# The backend code was copied to /app/backend in the builder stage
COPY --from=builder /app/backend /app/backend
# Ensure __init__.py exists in relevant dirs if needed for package discovery

# Set permissions for the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn
# Points to the FastAPI app instance in backend/app/main.py
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"] 