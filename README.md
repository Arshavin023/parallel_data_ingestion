# File Ingestion Process

![System Architecture](images/ingestion_architecture.jpg)

## Overview
The core objective of this system is to bridge the gap between raw edge-node data (JSON) and a structured Data Warehouse, while strictly managing the physical and logical storage footprint.

#### Key Components
- Parallel Ingestion Engine: Utilizes concurrent workers to monitor and ingest JSON files from facility-specific directories into the database.
- Partitioned Staging Layer: Data is loaded into staging tables partitioned by Facility_ID (List Partitioning) to facilitate rapid downstream processing and easy management.
- Source Cleanup Pipeline: A post-ingestion trigger that identifies successfully processed files and removes them from the local file system to prevent disk saturation.
- Staging Purge Pipeline: A synchronization-aware cleanup process that deletes records from the staging environment only after verification of a successful migration to the remote Data Warehouse.

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Deployment](#deployment)
- [License](#license)
- [Contributing](#contributing)  
- [Authors & Acknoledgements](#authors_and_acknowledgments)

## Introduction <a name="introduction"></a>
In modern healthcare informatics, the ability to process high volumes of facility-specific data with low latency is critical. This project implements a high-performance Concurrent Data Ingestion Pipeline designed to ingest JSON-based clinical records from multiple source directories into a centralized staging environment. 
The system is engineered to handle data from various hospital facilities simultaneously, utilizing List Partitioning to ensure data isolation, security, and query optimization. Beyond ingestion, the framework incorporates automated Data Lifecycle Management (DLM) pipelines to maintain storage hygiene by purging processed files and archived staging records, ensuring the system remains performant and cost-effective.

## Installation <a name="installation"></a>
#### Prerequisites <a name="prerequisites"></a>
Before running the File Ingestion Process, ensure you have the following prerequisites installed:
- Database: A SQL instance supporting partitioning (e.g., PostgreSQL 14+).
- Environment: Python 3.9+ with pip installed.
- Storage: Read/Write permissions on all source JSON directories.

## Configuration <a name="configuration"></a>
Create database_credentials file and fill in the info
```
nano /home/server_user/database_credentials/config.ini
[database]
ods_host=localhost
ods_port=5432
ods_username=database_username
ods_password=database_password
ods_database_name=database_name

stg_host=localhost
stg_port=5432
stg_username=database_username
stg_password=database_password
stg_database_name=database_name
```

## Usage <a name="usage"></a>
Navigate to server_user folder and create virtual environment
```
cd /home/server_user
python3 -m venv server_user_venv
```

Clone the repository to your local machine:
``` 
git clone https://github.com/Data-Fi-Nigeria-server_user/server_user_sync_ingestion.git
```

Navigate to the ingestion pipeline directory:
``` 
mkdir server_user_sync_ingestion && cd server_user_sync_ingestion
```

Create a Virtual & Activate Environment
```
python3 -m venv lamisplus_venv
source lamisplus_venv/bin/activate
```

Install the required Python packages:
```
pip install -r requirements.txt
```

Run Ingestion Pipeline Manually to test
```
cd ingestion_pipeline/records_ingestion/old
nohup python file_ingestion_process.py &
nohup python dsd_ingestion_process.py &
```

## Deployment <a name="deployment"></a>
Automate bash scripts to run periodically
```
crontab -e
*/30 * * * * /home/lamisplus/ingestion_pipeline/records_ingestion/orchestrate_file_ingestion.sh
*/15 * * * * /home/lamisplus/ingestion_pipeline/records_ingestion/orchestrate_dsd_file_ingestion.sh
#0 */2 * * * /home/lamisplus/lamisplus_ingestion_pipeline/run_report_summary.sh
0 2 * * * /home/lamisplus/ingestion_pipeline/records_deletion/orchestrate_stg_record_delete.sh
0 3 1 * * /home/lamisplus/ingestion_pipeline/file_deletion/orchestrate_file_delete.sh
```

## License <a name="license"></a>
- MIT License

## Authors & Acknowledgements <a name="authors_and_acknowledgments"></a>
- [Uche Nnodim](https://github.com/Arshavin023)
- [Emmanuel Nnajiofor](https://github.com/emmannajichi)
- [ChukwuEmeka Ilozie](https://github.com/Asquarep)
- [Peter Abiodun](https://github.com/drjavanew)
- [Barnabas Tyav](https://github.com/tyavbarnabas)



