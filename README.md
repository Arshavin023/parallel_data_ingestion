# File Ingestion Process

![System Architecture](images/ingestion_architecture.png)

## Overview

This project implements a high-performance, containerized pipeline for ingesting JSON-based clinical records from facility-specific edge nodes into a partitioned PostgreSQL staging environment. Built for the LAMISPlus/DataFI platform, it combines Python multithreading for concurrent file processing with automated data lifecycle management — ensuring the system remains performant and storage-efficient at scale.

#### Key Components

- **Parallel Ingestion Engine:** Python multithreading drives concurrent workers that monitor and ingest JSON files from facility-specific source directories into partitioned staging tables, maximizing throughput across hundreds of facilities simultaneously.
- **Partitioned Staging Layer:** Records land in staging tables partitioned by `Facility_ID` (List Partitioning), enabling rapid downstream processing, data isolation per facility, and efficient query pruning.
- **Schema Alignment Module:** A cross-server schema synchronization utility (`schema_alignment.py`) ensures staging table structures remain consistent with the source before ingestion begins.
- **Source Cleanup Pipeline:** A post-ingestion service that identifies successfully processed JSON files and removes them from the local filesystem to prevent disk saturation on edge nodes.
- **Staging Purge Pipeline:** A synchronization-aware deletion process that removes records from the staging environment only after verifying successful migration to the remote Data Warehouse.
- **Containerized Services:** All pipeline stages are packaged as Docker services, enabling reproducible deployments and independent scheduling of each stage via `docker compose`.
- **Test Coverage:** A `pytest` suite covering all production modules — ingestion, file deletion, and records deletion — with shared fixtures via `conftest.py`.

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Module Reference](#module-reference)
- [Docker Services](#docker-services)
- [Scheduling](#scheduling)
- [License](#license)
- [Authors & Acknowledgements](#authors--acknowledgements)

## Introduction

In modern healthcare informatics, the ability to process high volumes of facility-specific data with low latency is critical. This project implements a high-performance Concurrent Data Ingestion Pipeline designed to ingest JSON-based clinical records from multiple source directories into a centralized staging environment serving the LAMISPlus platform across ~599 PEPFAR-supported facilities.

The system is engineered to handle data from multiple hospital facilities simultaneously, utilizing List Partitioning to ensure data isolation, security, and query optimization. Beyond ingestion, the framework incorporates automated Data Lifecycle Management (DLM) pipelines to maintain storage hygiene by purging processed files and archived staging records, ensuring the system remains performant and cost-effective over time.

## Prerequisites

Before running the File Ingestion Process, ensure the following are available:

- **Runtime:** Python 3.9+ with `pip` installed
- **Containerization:** Docker and Docker Compose installed and running
- **Database:** PostgreSQL 14+ with partitioning support; read/write access on all staging schemas
- **Storage:** Read/write permissions on all source JSON directories
- **Credentials:** A `.env` file at `/home/server_user/lamisplus_ingestion/.env` with database connection parameters

## Installation

Navigate to the server user's home directory:

```bash
cd /home/server_user
```

Clone the repository:

```bash
git clone https://github.com/Arshavin023/parallel_data_ingestion.git
cd parallel_data_ingestion
```

Install Python dependencies (for local development or testing outside Docker):

```bash
pip install -r requirements.txt
```

## Configuration

Create the environment file with database connection parameters:

```bash
nano /home/server_user/lamisplus_ingestion/.env
```

```env
# Database connection settings
DB_USER=database_username
DB_PASSWORD=database_password
DB_PORT=6432

# Database names used by pipeline scripts
DB_NAME_FILEDB=filedb
DB_NAME_LAMISPLUS_STAGING_DWH=lamisplus_staging_dwh
```

## Usage

Build and run pipeline services using Docker Compose:

```bash
# Tear down any existing containers and prune stale networks
docker compose down
docker network prune -f

# Build all service images from scratch
docker compose build --no-cache

# Run each pipeline stage independently
docker compose run --rm file-ingestion-service
docker compose run --rm records-deletion-service
docker compose run --rm file-deletion-service
```

To run the test suite locally:

```bash
pytest tests/ -v
```

## Module Reference

Production modules are organized by pipeline stage. Each stage has a current production implementation and archived `old/` variants retained for reference.

### Ingestion

| Module | Function |
|---|---|
| `records_ingestion/multithread_file_loader_v3.py` | Current production multithreaded file loader; spawns concurrent workers per facility directory |
| `records_ingestion/multi_file_ingestion_process_v2.py` | Orchestrates the ingestion run, coordinates worker threads, and handles per-file status tracking |
| `records_ingestion/schema_alignment.py` | Cross-server schema synchronization; aligns staging table structures with source before ingestion |

### File Deletion

| Module | Function |
|---|---|
| `file_deletion/multi_automate_file_delete_v2.py` | Identifies successfully ingested source JSON files eligible for deletion |
| `file_deletion/multi_file_deletion_process_v2.py` | Executes concurrent deletion of processed files from facility source directories |

### Records Deletion

| Module | Function |
|---|---|
| `records_deletion/stg_records_deletion_process.py` | Verifies successful migration to the Data Warehouse, then purges corresponding staging records |

### Database Connection

| Module | Function |
|---|---|
| `database_connection/connect_to_db.py` | Base database connection utility |
| `database_connection/connect_to_db_v2.py` | Production connection utility with improved error handling and context manager support |

### Tests

| Test Module | Covers |
|---|---|
| `tests/test_multithread_file_loader_v3.py` | Concurrent file loader logic and worker thread behavior |
| `tests/test_multi_file_ingestion_process_v2.py` | End-to-end ingestion orchestration and status tracking |
| `tests/test_multi_automate_file_delete_v2.py` | File eligibility detection for post-ingestion deletion |
| `tests/test_multi_file_deletion_process_v2.py` | Concurrent file deletion execution |
| `tests/test_stg_records_deletion_process.py` | Staging purge logic and warehouse verification checks |

## Docker Services

All pipeline stages are defined as independent Docker services in `docker-compose.yml`:

| Service | Stage | Description |
|---|---|---|
| `file-ingestion-service` | Ingestion | Runs the concurrent JSON file ingestion pipeline into partitioned staging tables |
| `records-deletion-service` | Staging Purge | Deletes staging records verified as successfully migrated to the Data Warehouse |
| `file-deletion-service` | Source Cleanup | Removes processed JSON files from facility source directories after confirmed ingestion |

## Scheduling

Each Docker service is scheduled independently via system cron, with offsets to distribute database load:

```bash
crontab -e

# 1. Run file ingestion every 30 minutes
*/30 * * * * cd /home/server_user/lamisplus_ingestion && /usr/local/bin/docker-compose run --rm file-ingestion-service

# 2. Run staging records deletion daily at midnight
0 0 * * * cd /home/server_user/lamisplus_ingestion && /usr/local/bin/docker-compose run --rm records-deletion-service

# 3. Run source file deletion every Sunday at 2:00 AM
0 2 * * 0 cd /home/server_user/lamisplus_ingestion && /usr/local/bin/docker-compose run --rm file-deletion-service
```

> The `dsd-ingestion-service` referenced in earlier pipeline versions has been consolidated into the current `file-ingestion-service`. Update cron entries if your deployment still runs a separate DSD service.

## License

MIT License

## Authors & Acknowledgements

- [Uche Nnodim](https://github.com/Arshavin023)
- [Emmanuel Nnajiofor](https://github.com/emmannajichi)
- [ChukwuEmeka Ilozie](https://github.com/Asquarep)
- [Peter Abiodun](https://github.com/drjavanew)
- [Barnabas Tyav](https://github.com/tyavbarnabas)