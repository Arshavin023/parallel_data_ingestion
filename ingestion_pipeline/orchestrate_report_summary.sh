#!/bin/bash

# Change to the directory where your Python script is located
sudo su

cd /home/lamisplus/lamisplus_ingestion_pipeline

# Activate virtual environment
source lamisplus_venv/bin/activate

# Run the Python script
python pcs_summary_report.py
