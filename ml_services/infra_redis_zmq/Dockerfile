FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY publisher.py subscriber.py ./

# Expose ZeroMQ port
EXPOSE 5556

# Default command - can be overridden with docker run command
# Use an entrypoint script to determine which file to run
ENTRYPOINT ["python"]

# Default to publisher if no argument provided
CMD ["publisher.py"]
