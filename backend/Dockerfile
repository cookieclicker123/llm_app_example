# Stage 1: Build environment with dependencies
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build tools
RUN pip install --upgrade pip
RUN pip install build # Needed to build the package from pyproject.toml

# Copy project definition (relative to root context)
COPY pyproject.toml ./ 

# Copy the backend source code (relative to root context)
# Note: .dockerignore should prevent copying .venv etc.
COPY ./backend /app/backend 

# Now install dependencies, which will also install the local package
RUN pip install ".[test]" # Install with test dependencies for running tests later

# --- DEBUG: Check installation --- #
RUN echo "---> Builder Stage: Listing site-packages/backend..."
RUN ls -l /usr/local/lib/python3.11/site-packages/backend || echo "backend directory not found in site-packages"
RUN echo "---> Builder Stage: Running pip list..."
RUN pip list
# --- END DEBUG --- #

# (Optional) Run tests within the build stage to fail early
# RUN .venv/bin/python -m pytest 

# Stage 2: Final runtime environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user and group
RUN addgroup --system app && adduser --system --ingroup app app

# Copy installed dependencies (libraries AND executables) from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code from the builder stage
# This might conflict with the installed package when using --reload and volumes
# Commenting out for now - rely on the installed package in site-packages
# COPY --from=builder /app/backend /app/backend 

# Set permissions for the non-root user
# Need to ensure /app exists and is owned by app user for potential volume mounts etc.
# RUN mkdir /app && chown app:app /app # Redundant if WORKDIR /app already exists? Check.
RUN chown -R app:app /app # Ensure ownership of WORKDIR /app
 
# Switch to the non-root user
USER app

# Ensure final WORKDIR is /app
WORKDIR /app

# Expose the port the app runs on
EXPOSE 8000

# --- DEBUG: Check Python Path at Runtime --- #
RUN echo "---> Final Stage: Checking Python Path..."
RUN python -c "import sys; print(sys.path)"
# --- END DEBUG --- #

# Command to run the application using uvicorn
# Points to the FastAPI app instance using the installed package path
# Runs from WORKDIR /app
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]