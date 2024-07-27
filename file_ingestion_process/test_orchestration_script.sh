#!/bin/bash

# Define the path to your Python script
cd /home/lamisplus || exit 1

source lamisplus_venv/bin/activate || exit 1

SCRIPT_PATH="/home/lamisplus/lamisplus_ingestion_pipeline/test_run_ingestion_process.py"

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


#pgrep -l -f "test_run_ingestion_process.py"

#0 * * * * /home/lamisplus/lamisplus_ingestion_pipeline/filedb_file_deletion_process/orchestration_script.sh

#0 * * * * /home/lamisplus/lamisplus_ingestion_pipeline/filedb_file_deletion_process/orchestration_script.sh >> /home/lamisplus/lamisplus_ingestion_pipeline/logs/ngestion_logfile.log 2>&1

#*/10 * * * *

#0 * * * * /home/lamisplus/lamisplus_ingestion_pipeline/filedb_file_deletion_process/orchestration_script.sh >> /home/lamisplus/lamisplus_ingestion_pipeline/logs/ingestion_logfile.log 2>&1
