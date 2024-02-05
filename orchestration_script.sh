#!/bin/bash

# Define the path to your Python script
SCRIPT_PATH=/home/oluwaloseyi/run_ingestion_process.py

# Function to check if the pipeline is running
is_pipeline_running() {
    process_command="run_ingestion_process.py"
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


#pgrep -l -f "run_ingestion_process.py"

#0 * * * * /path/to/orchestration_script.sh

#0 * * * * /home/oluwaloseyi/orchestration_script.sh >> /home/oluwaloseyi/ingestion_logfile.log 2>&1

#*/10 * * * *

#0 * * * * /home/oluwaloseyi/orchestration_script.sh >> /home/oluwaloseyi/ingestion_logfile.log 2>&1
