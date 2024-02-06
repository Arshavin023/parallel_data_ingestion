#!/bin/bash

# Define the path to your Python script
SCRIPT_PATH=/home/oluwaloseyi/filedb_file_deletion_process/run_deletion_process.py

# Function to check if the pipeline is running
is_pipeline_running() {
    process_command="run_deletion_process.py"
    pgrep -f "$process_command">/dev/null
}

# Check if the pipeline is running
if is_pipeline_running; then
    echo "Pipeline is already running. Exiting."
    exit 0
else
    echo "Starting the pipeline..."
    python3 $SCRIPT_PATH
fi
