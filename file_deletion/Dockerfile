FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for compiling packages like psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the file deletion logic and shared modules
COPY file_deletion/ ./file_deletion/
COPY database_connection/ ./database_connection/
COPY src/ ./src/

ENV PYTHONPATH="/app"

# Execute directly via Python execution
CMD ["python", "file_deletion/multi_file_deletion_process.py"]