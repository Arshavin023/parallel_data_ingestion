import json
import os
from datetime import datetime
from src import logger
from database_connection import connect_to_db

file_directory = os.environ.get('FILE_DIRECTORY')


class FileDelete:
    """
    Deletes encrypted and decrypted JSON files that have already been ingested,
    logging every deletion attempt to file_deletion_log.

    Connection strategy — ONE connection per facility, passed into every helper.
    This replaces the original pattern of opening a new connection per log call,
    which exhausted PgBouncer under multithreaded load.
    """

    def __init__(self):
        self.facility_id = None
        self.demo_path = file_directory
        self.delete_start_time = None
        self.delete_end_time = None

    # ── Table-name helper ──────────────────────────────────────────────────────

    @staticmethod
    def _derive_tablename(file_path: str) -> str:
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        non_digit_parts = [p for p in parts if not p.isdigit() and p != 'decrypted.json']
        return '_'.join(non_digit_parts)

    # ── Audit log helpers — accept an open connection, never open their own ───

    def _insert_into_log(self, conn, table_name: str, file_name: str, facility_id: str) -> int:
        """
        Insert a 'processing' row into file_deletion_log.
        Uses the caller's connection — does NOT open a new one.
        Returns the new row id.
        """
        insert_query = """
            INSERT INTO file_deletion_log
                (deletion_start_time, deletion_status_check, table_name, file_name, facility_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        with conn.cursor() as cur:
            cur.execute(insert_query, (
                self.delete_start_time, 'processing',
                table_name, file_name, facility_id,
            ))
            log_id = cur.fetchone()[0]
        conn.commit()
        return log_id

    def _update_log(self, conn, log_id: int, proc_status: str,
                    file_name: str, error_msg: str, facility_id: str) -> None:
        """
        Update file_deletion_log with final status.
        Uses the caller's connection — does NOT open a new one.
        """
        update_query = """
            UPDATE public.file_deletion_log
            SET deletion_end_time     = %s,
                deletion_status_check = %s,
                json_rec_count        = %s,
                error_message         = %s
            WHERE id = %s AND facility_id = %s
        """
        with conn.cursor() as cur:
            cur.execute(update_query, (
                self.delete_end_time, proc_status,
                0, error_msg,
                log_id, facility_id,
            ))
        conn.commit()
        logger.info('%s log updated — %s', file_name, proc_status)

    # ── File deletion ──────────────────────────────────────────────────────────

    def _delete_single_file(self, conn, log_id: int,
                             local_path: str, file_name: str) -> None:
        """
        Delete one file and update its audit log row.
        All DB work uses the shared `conn`.
        """
        if os.path.exists(local_path):
            logger.info("Deleting: %s", local_path)
            os.remove(local_path)
            self.delete_end_time = datetime.now()
            self._update_log(conn, log_id, 'success', file_name, 'no errors', self.facility_id)
        else:
            logger.error("Not found: %s", local_path)
            self.delete_end_time = datetime.now()
            self._update_log(conn, log_id, 'failed', file_name, 'file not found', self.facility_id)

    # ── Main entry point ───────────────────────────────────────────────────────

    def delete_encrypted_files(self, facility_id: str) -> None:
        """
        Query sync_file for files that have been ingested but not yet deleted,
        then delete both the encrypted and decrypted copies from disk.

        ONE connection is opened for the entire facility run and reused for
        every insert/update call. This is the key fix — the original code opened
        a new connection for every _insert_into_log and _update_log call, which
        exhausted PgBouncer under concurrent load and caused 'Cannot assign
        requested address' errors that destabilised the database.
        """
        retrieve_query = """
            SELECT sf.facility_id, sf.file_name, sf.ingest_file_name
            FROM public.sync_file sf
            WHERE sf.processed IN (2, -2)
              AND sf.modified_date >= CURRENT_DATE - INTERVAL '240 DAYS'
              AND sf.modified_date <= CURRENT_DATE - INTERVAL '1 DAYS'
              AND sf.ingest_end_time IS NOT NULL
              AND sf.file_name IS NOT NULL
              AND sf.facility_id = %s
              AND NOT EXISTS (
                  SELECT 1
                  FROM public.file_deletion_log fdl
                  WHERE fdl.file_name = sf.file_name
                    AND fdl.facility_id = %s
                    AND fdl.deletion_status_check IN ('success', 'failed')
                    AND fdl.file_name NOT ILIKE '%%_decrypted%%'
              )
        """
        # One connection for the whole facility — reused by every helper call
        with connect_to_db.connect('filedb')[0] as conn:
            with conn.cursor() as cur:
                cur.execute(retrieve_query, (facility_id, facility_id))
                files = cur.fetchall()

            if not files:
                logger.info("No files pending deletion for %s", facility_id)
                return

            for fac_id, enc_name, dec_name in files:
                self.facility_id = fac_id
                self.delete_start_time = datetime.now()

                enc_path = os.path.join(self.demo_path, fac_id, enc_name)
                dec_path = os.path.join(self.demo_path, fac_id, dec_name)

                # Insert audit rows — using the shared connection
                enc_log_id = self._insert_into_log(
                    conn, self._derive_tablename(enc_path), enc_name, fac_id
                )
                dec_log_id = self._insert_into_log(
                    conn, self._derive_tablename(dec_path), dec_name, fac_id
                )

                try:
                    self._delete_single_file(conn, enc_log_id, enc_path, enc_name)
                    self._delete_single_file(conn, dec_log_id, dec_path, dec_name)

                except PermissionError as exc:
                    self.delete_end_time = datetime.now()
                    err = f"Permission error: {exc}"
                    logger.error(err)
                    self._update_log(conn, enc_log_id, 'failed', enc_name, err, fac_id)
                    self._update_log(conn, dec_log_id, 'failed', dec_name, err, fac_id)

                logger.info('-' * 90)
