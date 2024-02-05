# File Ingestion Process
Overview
The File Ingestion Process is a Python-based data pipeline designed to ingest JSON files into a PostgreSQL database. This README provides an overview of the key components and functionality of the pipeline.

# Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#Prerequisites)
- [Installation](#Installation)
- [Usage](#Usage)
- [Configuration](#Configuration)
- [File Structure](#File Structure)
- [Contributing](#Contributing)
- [License](#License)


## Introduction <a name="introduction"></a>
The File Ingestion Process consists of Python scripts that facilitate the ingestion of JSON files into a PostgreSQL database. It leverages the psycopg2 library for database connectivity and the pandas library for data manipulation.

## Prerequisites <a name="Prerequisites"></a>
Before running the File Ingestion Process, ensure you have the following prerequisites installed:

- Python 3.x
- PostgreSQL database
- psycopg2 library (pip install psycopg2)
- pandas library (pip install pandas)

## Installation <a name="Installation"></a>

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

## Usage <a name="Usage"></a>
To use the File Ingestion Process, follow these steps:

- Update the database connection parameters in the Python scripts (file_ingestion_loader.py and run_ingestion_process.py) to match your PostgreSQL database configuration.

- Place your JSON files to be ingested into the designated directory (/home/lamisplus/server/temp by default).

- Run the pipeline orchestration script (orchestration_script.sh) to start the ingestion process:

```
./orchestration_script.sh
```

## Configuration <a name="Configuration"></a>
The configuration of the File Ingestion Process can be customized by modifying the following parameters in the Python scripts:

- Database connection parameters (host, database, user, password, port)

- Directory for storing JSON files (demo_path in file_ingestion_loader.py)

- JSON file processing logic and data manipulation (in file_ingestion_loader.py)

## File Structure <a name="File Structure"></a>
The File Ingestion Process repository has the following structure:

**lamisplus_sync_ingestion_process** ---> *file_ingestion_loader.py* >> *run_ingestion_process.py* >> *orchestration_script.sh*


- **file_ingestion_loader.py**: Python script responsible for ingesting JSON files into the PostgreSQL database.

- **run_ingestion_process.py**: Python script to execute the file ingestion process.

- **orchestration_script.sh**: Bash script to orchestrate the execution of the ingestion process.

## Contributing <a name="Contributing"></a>
Contributions to the File Ingestion Process project are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request on GitHub.

## License <a name="License"></a>
This project is licensed under the MIT License - see the LICENSE file for details.