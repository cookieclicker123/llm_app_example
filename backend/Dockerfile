# Base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app

# Expose port
EXPOSE 8000

# Command to run the application (using uvicorn)
# This assumes your FastAPI app instance is named `app` in `main.py`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 