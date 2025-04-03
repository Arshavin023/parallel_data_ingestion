#!/bin/bash

# Database credentials
DB_USER="lamisplus"
DB_PASSWORD="#&3k4PFZ3Tuv"
DB_NAME="appdb"
DB_HOST="localhost"  # or the IP address of your database server
DB_PORT="5432"       # default PostgreSQL port

# Stored procedure to call
PROCEDURE_NAME="proc_update_sync_queue_tracker_refresh"

# Export the password to avoid prompting for it
export PGPASSWORD="$DB_PASSWORD"

# Command to run the stored procedure
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -p "$DB_PORT" -c "CALL $PROCEDURE_NAME();" >> /home/uche/logs/run_procedure.log 2>&1
