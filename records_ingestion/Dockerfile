FROM python:3.10-slim

WORKDIR /app

# Install system dependencies needed for compiling packages like psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration metadata from the root repository layout
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the ingestion logic and shared module folder
COPY records_ingestion/ ./records_ingestion/
COPY database_connection/ ./database_connection/
COPY src/ ./src/

ENV PYTHONPATH="/app"