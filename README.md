# File Ingestion Process
## Overview
The File Ingestion Process is a Python-based data pipeline designed to ingest JSON files into a PostgreSQL database. This README provides an overview of the key components and functionality of the pipeline.

# Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Process Overview](#process-overview)
- [Usage](#usage)
- [Configuration](#configuration)
- [File-Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)   
- [Improvements](#improvements)


## Introduction <a name="introduction"></a>
The File Ingestion Process consists of Python scripts that facilitate the ingestion of JSON files into a PostgreSQL database. It leverages the psycopg2 and sqlalchemy libraries for database connectivity and the pandas library for data manipulation.

## Prerequisites <a name="prerequisites"></a>
Before running the File Ingestion Process, ensure you have the following prerequisites installed:

- Python 3.x
- PostgreSQL database
- psycopg2 library (pip install psycopg2)
- pandas library (pip install pandas)
- sqlalchemy (pip install sqlalchemy)

## Installation <a name="installation"></a>

Clone the repository to your local machine:

``` 
git clone https://github.com/Data-Fi-Nigeria-LAMISPlus/lamisplus_sync_ingestion_pipeline.git
```

Navigate to the project directory:


``` 
cd lamisplus_sync_ingestion_process
```

Install the required Python packages:

```
pip install -r requirements.txt
```

## Process Overview <a name="process-overview"></a>

This process consists of two parts: 
a Python script for data ingestion and processing, and a Bash script for orchestrating the execution of the Python script.

### Python Script (Data Ingestion and Processing)
This Python script defines a class FileLoader with methods for ingesting JSON data into a PostgreSQL database, logging ingestion activities, and updating related tables. Here's a breakdown of the key processes

[Use this link for a further breakdown of the FileLoader class](FileLoader_Deep_Dive.md)

#### Initialization and Setup

The FileLoader class initializes attributes such as facility_id, syncfile_entryID, and directory paths.
Database connection parameters are defined in methods _db_connect and _db_connect_filedb.

- Database Operations
Methods _get_and_map_cols, _insert_into_log, _fakeupsert_synclog, _update_log, _update_flag_syncfile, and _update_centralpartnermapper handle database operations such as retrieving column information, inserting log entries, and updating flags in the sync file.

- File Processing
Methods _retrieve_localdir_from_syncfile, _process_derive_tablename, and _process_file_by_name manage file processing tasks. Files are retrieved from the sync file, processed based on their names, and ingested into the database.

- Data Ingestion
Method _ingest_json_data reads JSON files, converts PostgreSQL data types to SQLAlchemy data types, and ingests the data into staging tables in the database.

- Bash Script (Orchestration)
The Bash script is responsible for orchestrating the execution of the Python script. It checks whether the pipeline is already running and starts the pipeline if it's not running.

#### Execution Flow
The Bash script checks if the pipeline is already running. If it is, the script exits. Otherwise, it starts the pipeline by executing the Python script.
The Python script initializes, connects to the database, retrieves files from the sync file, processes each file, and ingests data into the database.

In case of errors during data processing, appropriate error handling and logging are performed.

After processing all files, the Python script updates the pipeline log with the execution status (success or failure).

The Bash script is scheduled to run periodically using cron.

Overall, this setup orchestrates the ingestion and processing of data files into a PostgreSQL database and ensures proper error handling and logging during the process.

## Usage <a name="usage"></a>
To use the File Ingestion Process, follow these steps

- Update the database connection parameters in the Python scripts (file_ingestion_loader.py and run_ingestion_process.py) to match your PostgreSQL database configuration.

- Place your JSON files to be ingested into the designated directory (/home/lamisplus/server/temp by default).

- Run the pipeline orchestration script (orchestration_script.sh) to start the ingestion process

```
./orchestration_script.sh
```

## Configuration <a name="configuration"></a>
The configuration of the File Ingestion Process can be customized by modifying the following parameters in the Python scripts

- Database connection parameters (host, database, user, password, port)

- Directory for storing JSON files (demo_path in file_ingestion_loader.py)

- JSON file processing logic and data manipulation (in file_ingestion_loader.py)

## File Structure <a name="file-structure"></a>
The File Ingestion Process repository has the following structure

**lamisplus_sync_ingestion_process** --->*file_ingestion_loader.py*>> *run_ingestion_process.py* >> *orchestration_script.sh*


- **file_ingestion_loader.py**: Python script responsible for ingesting JSON files into the PostgreSQL database.

- **run_ingestion_process.py**: Python script to execute the file ingestion process.

- **orchestration_script.sh**: Bash script to orchestrate the execution of the ingestion process.

## Contributing <a name="contributing"></a>
Contributions to the File Ingestion Process project are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request on GitHub.

## License <a name="license"></a>
This project is licensed under the MIT License - see the LICENSE file for details.

## Improvements <a name="improvements"></a>

- To create a multithreading process flow. This will enable the job run multiple instances without file conflicts

- To fully orcheastrate workflow with **Apache Airflow**

- To consider the use of Distributed File Systems and Frameworks like Hadoop, Map-R, Apache Spark e.t.c. for Processing Big Data. 