#!/bin/bash

# Define the path to your Python script
SCRIPT_PATH="multi_file_deletion_process.py"
LOG_FILE="logs/file_deletion_pipeline.log"

# Change directory to your project directory
cd /home/lamisplus/lamisplus_ingestion || { echo "Error: Unable to change directory." >&2; exit 1; }

# Activate the virtual environment
source lamisplus_venv/bin/activate || { echo "Error: Unable to activate virtual environment." >&2; exit 1; }

# Change to project directory
cd /home/lamisplus/lamisplus_ingestion/file_deletion || { echo "Error: Unable to change directory." >&2; exit 1; }

# Check if the script file exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "$(date +"%Y-%m-%d %H:%M:%S"): Error: Python script '$SCRIPT_PATH' not found. Exiting." >> "$LOG_FILE"
    exit 1
fi

# Function to check if the pipeline is running
is_pipeline_running() {
    pgrep -f "$SCRIPT_PATH" >/dev/null
}

# Check if the pipeline is already running
if is_pipeline_running; then
    echo "$(date +"%Y-%m-%d %H:%M:%S"): Pipeline is already running. Exiting." >> "$LOG_FILE"
    exit 0
else
    echo "$(date +"%Y-%m-%d %H:%M:%S"): Starting the pipeline..." >> "$LOG_FILE"
    python3 "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1 &
    echo "$(date +"%Y-%m-%d %H:%M:%S"): Pipeline started successfully." >> "$LOG_FILE"
fi
