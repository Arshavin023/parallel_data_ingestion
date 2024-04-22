#!/bin/bash

# Define the path to your Python script
cd /home/lamisplus || exit 1

source lamisplus_venv/bin/activate || exit 1

SCRIPT_PATH="/home/lamisplus/lamisplus_ingestion_pipeline/run_ingestion_process.py"

# Function to check if the pipeline is running
is_pipeline_running() {
    pgrep -f "$SCRIPT_PATH" >/dev/null
}

# Check if the pipeline is running
if is_pipeline_running; then
    echo "Pipeline is already running. Exiting."
    exit 0
else
    echo "Starting the pipeline..."
    python3 "$SCRIPT_PATH"
fi