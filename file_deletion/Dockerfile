FROM python:3.10-slim

# Create a non-privileged system group and user inside the container image
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -m -s /bin/bash appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-create the logs directory while still running as root
RUN mkdir -p /app/file_deletion/logs

# Copy your application source code layers
COPY file_deletion/ ./file_deletion/
COPY database_connection/ ./database_connection/
COPY src/ ./src/

# Change ownership of the entire workspace directory to your new appuser
RUN chown -R appuser:appuser /app

# Switch the active running user context from root to appuser
USER appuser

ENV PYTHONPATH="/app"

# Execute safely as a non-root user
CMD ["python", "file_deletion/multi_file_deletion_process.py"]