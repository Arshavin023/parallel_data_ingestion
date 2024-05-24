#!/bin/bash

# Define the path to your Python script
SCRIPT_PATH="/home/lamisplus/lamisplus_ingestion_pipeline/run_stg_records_deletion_process.py"
LOG_FILE="/home/lamisplus/lamisplus_ingestion_pipeline/logs/deletion_stg_records_pipeline.log"

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