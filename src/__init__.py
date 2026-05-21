import os
import sys 
import logging

logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"

# 1. Dynamically find the absolute path of the directory containing 'src'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Automatically find the active service directory (e.g., file_deletion, records_ingestion, records_deletion)
# Default to the execution directory name if we can't find an explicit match
active_service = "records_ingestion" 
for folder in ["records_ingestion", "file_deletion", "records_deletion"]:
    if os.path.exists(os.path.join(BASE_DIR, folder)):
        active_service = folder
        break

log_dir = os.path.join(BASE_DIR, active_service, "logs")
log_filepath = os.path.join(log_dir, "running_logs.log")

# 3. Create the directory safely
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format=logging_str,
    handlers=[
        logging.FileHandler(log_filepath),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("mlProjectLogger")