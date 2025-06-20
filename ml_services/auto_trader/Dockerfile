FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
# Copy REST API service
COPY api.py .

# Create directory for logs
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV TRADE_MODE=manual
ENV CONFIDENCE_THRESHOLD=0.7
ENV MAX_RETRIES=3
ENV HEARTBEAT_INTERVAL=30
ENV DEFAULT_QUANTITY=1

# Expose API port
EXPOSE 8000

# Command to start BOTH the WebSocket auto-trader client **and** the FastAPI service
# 1. Launch the FastAPI server with Uvicorn on port 8000
# 2. Launch the auto-trader event loop (main.py)
# The `exec` form ensures proper signal handling for both processes.
#
# If either process exits, the container will stop (set ‑e) allowing Docker to
# restart it according to the restart policy.
CMD ["/bin/sh", "-c", "set -e; uvicorn api:app --host 0.0.0.0 --port 8000 & python main.py"]
