FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /app/model

# Copy application code
COPY main.py .

# Expose the port
EXPOSE 8002

# Command to run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
