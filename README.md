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
- [Automation](#automation)
- [Monitoring](#monitoring)
- [File-Structure](#file-structure)
- [Other-Supporting-Jobs](#other-supporting-jobs)
- [Contributing](#contributing)  
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

## Automation <a name="automation"></a>

Pipeline has been automated using the `crontab` functionality on linux

See support codes below

```
sudo crontab -e {edits crontab}

*/30 * * * * /home/oluwaloseyi/orchestration_script.sh >> /home/oluwaloseyi/ingestion_logfile.log 2>&1 {pipeline scheduled to run every 30 minutes}

sudo crontab -l {see available crontabs schedules}

```

## Monitoring <a name="monitoring"></a>

There are three monitoring levels. See below

1. Monitoring on the level of the job pipeline i.e. monitoring the jobs that runs the file ingestion pipeline. 
```
--lamisplus_staging_dwh (database in filedb)
select * from public.file_ingestion_pipeline_log; -- this logs holds information of the jobs for file_ingestion and file_deletions pieplines

```
2. Montoring on the ingestion level
These logs hold data of the ingestion process themselves.

```
--lamisplus_staging_dwh (database in filedb)
select * from public.file_ingestion_log;


--filedb (database in filedb)
--table shows processed status using 'processed' column 
-1 - file in decryption queue
-2 - decryption or ingestion failed
0 - uploaded
1 - decrypted
2 - ingested

select * from public.sync_file;
```
3. Montoring on the level of files inserted
```
--lamisplus_staging_dwh (database in filedb)
select * from public.stg_monitoring
```

## File Structure <a name="file-structure"></a>
The File Ingestion Process repository has the following structure

**lamisplus_sync_ingestion_process** --->*file_ingestion_loader.py*>> *run_ingestion_process.py* >> *orchestration_script.sh*


- **file_ingestion_loader.py**: Python script responsible for ingesting JSON files into the PostgreSQL database.

- **run_ingestion_process.py**: Python script to execute the file ingestion process.

- **orchestration_script.sh**: Bash script to orchestrate the execution of the ingestion process.

## Other Supporting Jobs <a name="other-supporting-jobs"></a>

There two (2) other supporting pipelines that support the ingestion process.

1. The Ingestion Process Summary Report Pipeline :
This pipelines prepares a report every 30mins of the ingestion process usinf the sql script below

```
select count(id) Total_Files, 
SUM(CASE WHEN processed =2 THEN 1 ELSE 0 END) processed_count,
SUM(CASE WHEN processed =0 THEN 1 ELSE 0 END) just_uploaded,
SUM(CASE WHEN processed =-1 THEN 1 ELSE 0 END) decryption_queue,
SUM(CASE WHEN processed =1 THEN 1 ELSE 0 END) decrypted_complete,
SUM(CASE WHEN processed =-2 AND ingest_status_check is null THEN 1 ELSE 0 END) real_decryption_fails,
SUM(CASE WHEN processed =-2 AND ingest_status_check is not null THEN 1 ELSE 0 END) ingestion_fails,
min(create_date) first_upload_date,
max(create_date) latest_upload_date,
SUM(CASE WHEN processed =-2 THEN 1 ELSE 0 END) fails, CURRENT_TIMESTAMP check_data
FROM sync_file;
```

Job was also scheduled using linux's crontab --check crontab -l. 
crontab runs the pipeline `[pcs_summary_report](pcs_summary_report.py)` using `[run_report_summary](run_report_summary.sh)` shell script.

2. The Ingested Files Deletion Pipeline {` See pipeline in /home/oluwaloseyi/filedb_file_deletion_process`}: 
This pipeline checks the sync_file log in the filedb for files that have been ingested successfully and operates on two levels

- Deletes decrypted files automatically if they were ingested successfully

- Deletes the encrypted files themselves if they were ingested successfully and have been in the system for at least 30 days

Job was also scheduled using linux's crontab --check crontab -l. crontab runs the pipeline `[automate_file_delete](filedb_file_deletion_process/automate_file_delete.py)` using `[orchestrate_file_deletion](filedb_file_deletion_process/orchestrate_file_deletion.sh)`` shell script.

## Contributing <a name="contributing"></a>
Contributions to the File Ingestion Process project are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request on GitHub.


## Improvements <a name="improvements"></a>

- To create a multithreading process flow. This will enable the job run multiple instances without file conflicts

- To fully orcheastrate workflow with **Apache Airflow**

- To consider the use of Distributed File Systems and Frameworks like Hadoop, Map-R, Apache Spark e.t.c. for Processing Big Data. 