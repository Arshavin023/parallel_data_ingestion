#!/bin/bash

SCRIPT_PATH="multi_file_ingestion_process.py"
LOG_FILE="logs/file_pipeline.log"
LOCK_FILE="/tmp/file_ingestion_pipeline.lock"

# Ensure logs directory exists
mkdir -p logs

{
    echo "========== $(date +"%Y-%m-%d %H:%M:%S") =========="
    echo "User: $(whoami)"
    echo "Working Directory: $(pwd)"
    echo "Starting File Ingestion Pipeline"

    # Change to project base
    cd /home/lamisplus || { echo "Error: Unable to change directory."; exit 1; }

    # Activate virtual environment
    source lamisplus_venv/bin/activate || { echo "Error: Unable to activate virtual environment."; exit 1; }

    # Change to pipeline directory
    cd /home/lamisplus/ingestion_pipeline/records_ingestion || { echo "Error: Unable to change directory."; exit 1; }

    # Use flock to prevent concurrent runs
    (
        flock -n 200 || { echo "Pipeline is already running (lock exists). Exiting."; exit 1; }

        echo "$(date +"%Y-%m-%d %H:%M:%S"): Running pipeline..."
        if python3 "$SCRIPT_PATH"; then
            echo "$(date +"%Y-%m-%d %H:%M:%S"): Pipeline completed successfully."
        else
            echo "$(date +"%Y-%m-%d %H:%M:%S"): Pipeline failed. Check the log for details."
            exit 1
        fi
    ) 200>"$LOCK_FILE"

    echo "============================================="
} >> "$LOG_FILE" 2>&1
