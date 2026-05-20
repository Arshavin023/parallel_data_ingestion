# import os
# import sys 
# import logging

# logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"

# log_dir = "logs"

# log_filepath = os.path.join(log_dir,"running_logs.log")
# os.makedirs(log_dir,exist_ok=True)

# logging.basicConfig(
#     level= logging.INFO,
#     format= logging_str,

#     handlers= [
#         logging.FileHandler(log_filepath),
#         logging.StreamHandler(sys.stdout)
#     ]
# )

# logger = logging.getLogger("mlProjectLogger")


import os
import sys 
import logging

logging_str = "[%(asctime)s: %(levelname)s: %(module)s: %(message)s]"

# 1. Dynamically find the absolute path of the directory containing 'src'
# This ensures that no matter where the script is called from, the paths align perfectly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Put the logs folder inside 'records_ingestion' (or whatever your shared root directory is)
# If you want it directly in the shared package root directory, use BASE_DIR
log_dir = os.path.join(BASE_DIR, "records_ingestion", "logs")

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