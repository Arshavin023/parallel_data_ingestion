import concurrent.futures
from datetime import datetime

import psycopg2
from src import logger
# from database_connection import connect_to_db_v2 as connect_to_db
from database_connection import connect_to_db
from file_deletion.multi_automate_file_delete_v2 import FileDelete


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fetch_datim_ids(ip_name: str) -> list[str]:
    """Return all facility datim_ids for the given IP name."""
    with connect_to_db.connect('filedb')[0] as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT datim_id FROM central_partner_mapping WHERE ip_name = %s",
                (ip_name,),
            )
            return [row[0] for row in cur.fetchall()]


def _insert_pipeline_log(cur, log_id: str, start_time: datetime) -> None:
    cur.execute(
        """
        INSERT INTO file_ingestion_pipeline_log (log_id, start_time, status, process_type)
        VALUES (%s, %s, %s, %s)
        """,
        (log_id, start_time, 'Job Started', 'file deletion'),
    )


def _update_pipeline_log(cur, log_id: str, end_time: datetime,
                          status: str, error_message: str,
                          records_processed: int) -> None:
    cur.execute(
        """
        UPDATE file_ingestion_pipeline_log
        SET end_time = %s, status = %s, error_message = %s, records_processed = %s
        WHERE log_id = %s
        """,
        (end_time, status, error_message, records_processed, log_id),
    )


# ── Per-facility worker ────────────────────────────────────────────────────────

def _process_single_facility(facility_id: str) -> None:
    """
    Worker executed by the thread pool for one facility.
    Creates a fresh FileDelete instance (thread-safe — no shared state).
    """
    try:
        FileDelete().delete_encrypted_files(facility_id)
        logger.info("Deletion completed for %s", facility_id)
    except Exception:
        logger.exception("Deletion failed for %s", facility_id)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ip_names = ['ACE-1', 'ACE-2', 'ACE-3', 'ACE-4', 'CARE 1', 'CARE 2', 'ACE-5']

    # Fetch all facility IDs up front — one connection, before threads start
    all_datim_ids = []
    for ip in ip_names:
        all_datim_ids.extend(_fetch_datim_ids(ip))

    if not all_datim_ids:
        logger.info("No facilities found for deletion — exiting.")
        return

    start_time = datetime.now()
    log_id = f'DPID_{start_time.strftime("%Y%m%d_%H_%M")}'
    logger.info("Starting deletion pipeline — log ID: %s", log_id)

    # Open the pipeline audit connection once, keep it for the duration of main()
    with connect_to_db.connect('lamisplus_staging_dwh')[0] as dwh_conn:
        with dwh_conn.cursor() as dwh_cur:
            _insert_pipeline_log(dwh_cur, log_id, start_time)
            dwh_conn.commit()

        try:
            logger.info("Deletion started — %d facilities", len(all_datim_ids))
            delete_start = datetime.now()

            # Process in batches of 10, max 3 concurrent threads per batch.
            # Keeping max_workers=3 limits simultaneous DB connections to 3
            # (one shared connection per FileDelete instance) rather than the
            # original pattern which opened 4+ connections per facility.
            batch_size = 10
            for i in range(0, len(all_datim_ids), batch_size):
                batch = all_datim_ids[i: i + batch_size]
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    executor.map(_process_single_facility, batch)
                logger.info("Batch complete — %d facilities: %s", len(batch), batch)

            delete_end = datetime.now()

            # Count processed records from the filedb audit log
            with connect_to_db.connect('filedb')[0] as filedb_conn:
                with filedb_conn.cursor() as filedb_cur:
                    filedb_cur.execute(
                        """
                        SELECT COUNT(*) FROM file_deletion_log
                        WHERE deletion_start_time >= %s
                          AND deletion_end_time   <= %s
                        """,
                        (delete_start, delete_end),
                    )
                    records_processed = filedb_cur.fetchone()[0]

            with dwh_conn.cursor() as dwh_cur:
                _update_pipeline_log(
                    dwh_cur, log_id, delete_end,
                    'Job Passed', 'No Errors', records_processed,
                )
            dwh_conn.commit()
            logger.info("Deletion pipeline completed — %d records processed", records_processed)

        except Exception:
            end_time = datetime.now()
            logger.exception("Fatal error in deletion pipeline")
            with dwh_conn.cursor() as dwh_cur:
                _update_pipeline_log(dwh_cur, log_id, end_time, 'Job Failed', 'See logs', 0)
            dwh_conn.commit()


if __name__ == '__main__':
    main()
