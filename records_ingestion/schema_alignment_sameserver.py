"""
schema_alignment.py

Compares schema between ServerA (source) and ServerB (destination) and
automatically applies DDL changes to ServerB before ingestion runs.

Checks:
  - New tables in ServerA not present in ServerB  → CREATE TABLE
  - New columns in ServerA not present in ServerB → ALTER TABLE ... ADD COLUMN
  - Data type mismatches                           → ALTER TABLE ... ALTER COLUMN TYPE

NOTE: NOT NULL, UNIQUE, DEFAULT, and all other constraints are intentionally
excluded. Staging tables on ServerB are constraint-free and partitioned.

Usage (standalone):
    python schema_alignment.py

Integrated (called from multi_file_ingestion_process_v2.py main()):
    from schema_alignment import run_schema_alignment
    run_schema_alignment()
"""

import psycopg2
from dataclasses import dataclass, field
from typing import Optional
# from database_connection import connect_to_db_v2 as connect_to_db
from database_connection.schema_alignment_connect import connect as connect_to_db
from src import logger


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class ColumnInfo:
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool           # True  → NULL allowed
    column_default: Optional[str]
    ordinal_position: int


@dataclass
class SchemaDiff:
    new_tables: list[str] = field(default_factory=list)
    new_columns: list[ColumnInfo] = field(default_factory=list)
    type_changes: list[dict] = field(default_factory=list)   # {table, column, old_type, new_type}
    nullable_changes: list[dict] = field(default_factory=list)  # {table, column, old_nullable, new_nullable}


# ──────────────────────────────────────────────
# Schema fetching
# ──────────────────────────────────────────────

SCHEMA_QUERY = """
    SELECT
        c.table_name,
        c.column_name,
        c.udt_name          AS data_type,   -- native type name (e.g. int4, varchar, timestamp)
        (c.is_nullable = 'YES') AS is_nullable,
        c.column_default,
        c.ordinal_position
    FROM information_schema.columns c
    JOIN information_schema.tables t
        ON t.table_name = c.table_name
        AND t.table_schema = c.table_schema
    WHERE c.table_schema = 'public'
      AND t.table_type = 'BASE TABLE'
      AND t.table_name IN ('hts_encounter', 'hts_ict_contact', 'hts_ict_encounter', 'hiv_adherence_preparation', 'hiv_patient_transfer_in', 'hiv_enrollment_commencement', 'hiv_initial_clinical_evaluation', 'prophylaxis_screening', 'prophylaxis_initiation', 'prophylaxis_interruptions', 'prep_followup_visit', 'pep_followup_visit', 'pmtct_pregnancy_cycle', 'pmtct_anc', 'pmtct_enrollment', 'pmtct_delivery', 'pmtct_mother_visitation', 'pmtct_infant_information', 'pmtct_infant_visit', 'hiv_adherence_preparation', 'hiv_art_clinical', 'hiv_art_pharmacy', 'hiv_art_pharmacy_regimens', 'hiv_drug', 'hiv_eac', 'hiv_eac_out_come', 'hiv_eac_session', 'hiv_enrollment_commencement', 'hiv_initial_clinical_evaluation', 'hiv_observation', 'hiv_ovc_linkage', 'hiv_patient_tracker', 'hiv_patient_transfer_in', 'hiv_regimen', 'hiv_regimen_drug', 'hiv_regimen_resolver', 'hiv_regimen_type', 'hiv_status_tracker')
    ORDER BY c.table_name, c.ordinal_position;
"""

def fetch_schema(conn, prefix: str = "") -> dict[str, dict[str, ColumnInfo]]:
    schema: dict[str, dict[str, ColumnInfo]] = {}
    with conn.cursor() as cur:
        cur.execute(SCHEMA_QUERY)
        for row in cur.fetchall():
            col = ColumnInfo(
                table_name=f"{prefix}{row[0]}",
                column_name=row[1],
                data_type=row[2],
                is_nullable=row[3],
                column_default=row[4],
                ordinal_position=row[5],
            )
            schema.setdefault(col.table_name, {})[col.column_name] = col
    return schema

# ──────────────────────────────────────────────
# Diff computation
# ──────────────────────────────────────────────

def compute_diff(source: dict, dest: dict) -> SchemaDiff:
    diff = SchemaDiff()

    # normalize destination: remove stg_
    dest_normalized = {k.replace("stg_", ""): v for k, v in dest.items()}

    for table_name, src_cols in source.items():
        if table_name not in dest_normalized:
            diff.new_tables.append(f"stg_{table_name}")
            continue

        dest_cols = dest_normalized[table_name]

        for col_name, src_col in src_cols.items():
            if col_name not in dest_cols:
                src_col.table_name = f"stg_{table_name}"
                diff.new_columns.append(src_col)
                continue

            dest_col = dest_cols[col_name]

            if src_col.data_type != dest_col.data_type:
                diff.type_changes.append({
                    "table": f"stg_{table_name}",
                    "column": col_name,
                    "old_type": dest_col.data_type,
                    "new_type": src_col.data_type,
                })

    return diff

#def compute_diff(source: dict, dest: dict) -> SchemaDiff:
#    diff = SchemaDiff()
#
#    for table_name, src_cols in source.items():
#        if table_name not in dest:
#            diff.new_tables.append(table_name)
            # All columns in this table need to be created — tracked via new_tables
#            continue
#
#        dest_cols = dest[table_name]

#        for col_name, src_col in src_cols.items():
#            if col_name not in dest_cols:
#                diff.new_columns.append(src_col)
#                continue

#            dest_col = dest_cols[col_name]

#            if src_col.data_type != dest_col.data_type:
#                diff.type_changes.append({
#                    "table": table_name,
#                    "column": col_name,
#                    "old_type": dest_col.data_type,
#                    "new_type": src_col.data_type,
#                })

            # Nullable/NOT NULL constraints are intentionally ignored —
            # staging tables on ServerB are constraint-free.

#    return diff


# ──────────────────────────────────────────────
# DDL generation
# ──────────────────────────────────────────────

def _udt_to_sql(udt_name: str) -> str:
    """
    Map PostgreSQL udt_name values back to usable SQL type names.
    Extend this mapping if your schema uses additional types.
    """
    mapping = {
        "int2": "SMALLINT",
        "int4": "INTEGER",
        "int8": "BIGINT",
        "float4": "REAL",
        "float8": "DOUBLE PRECISION",
        "numeric": "NUMERIC",
        "bool": "BOOLEAN",
        "bpchar": "CHAR",
        "varchar": "VARCHAR",
        "text": "TEXT",
        "date": "DATE",
        "timestamp": "TIMESTAMP",
        "timestamptz": "TIMESTAMPTZ",
        "uuid": "UUID",
        "json": "JSON",
        "jsonb": "JSONB",
        "bytea": "BYTEA",
    }
    return mapping.get(udt_name, udt_name.upper())


# Staging audit columns appended to every newly created table
_STG_COLUMN_DEFS = (
    "    stg_batch_id   CHARACTER VARYING,\n"
    "    stg_load_time  TIMESTAMP WITHOUT TIME ZONE,\n"
    "    stg_file_name  CHARACTER VARYING,\n"
    "    stg_datim_id   CHARACTER VARYING"
)


def build_create_table_ddl(table_name: str, columns: dict[str, ColumnInfo]) -> str:
    """
    Builds a CREATE TABLE DDL for ServerB.

    Every new table:
      - Has the four staging audit columns appended (stg_batch_id, stg_load_time,
        stg_file_name, stg_datim_id).
      - Is partitioned by LIST on stg_datim_id so partitions can be created
        per facility/datim ID at load time.

    NOTE: Intentionally excludes PRIMARY KEY, UNIQUE, FOREIGN KEY, and CHECK
    constraints. The destination staging schema is append-only and partitioned;
    constraints from the source are not appropriate here.

    To attach a partition later:
        CREATE TABLE "<table>_<datim_id>"
            PARTITION OF "<table>"
            FOR VALUES IN ('<datim_id>');
    """
    col_defs = []
    for col in sorted(columns.values(), key=lambda c: c.ordinal_position):
        sql_type = _udt_to_sql(col.data_type)
        # No NOT NULL / DEFAULT — staging tables are constraint-free
        col_defs.append(f'    {col.column_name} {sql_type}')

    col_defs.append(_STG_COLUMN_DEFS)
    cols_sql = ",\n".join(col_defs)

    return (
        f'CREATE TABLE IF NOT EXISTS {table_name} (\n{cols_sql}\n)'
        f" PARTITION BY LIST (stg_datim_id);"
    )


def build_ddl_statements(diff: SchemaDiff, source_schema: dict) -> list[str]:
    statements = []

    # 1. New tables
    for table_name in diff.new_tables:
        ddl = build_create_table_ddl(table_name, source_schema[table_name])
        statements.append(ddl)
        logger.info(f"[SCHEMA] Will CREATE TABLE: {table_name}")

    # 2. New columns
    for col in diff.new_columns:
        sql_type = _udt_to_sql(col.data_type)
        # No NOT NULL / DEFAULT — staging tables are constraint-free
        ddl = (
            f'ALTER TABLE {col.table_name} '
            f'ADD COLUMN IF NOT EXISTS {col.column_name} {sql_type};'
        )
        statements.append(ddl)
        logger.info(f"[SCHEMA] Will ADD COLUMN: {col.table_name}.{col.column_name} ({sql_type})")

    # 3. Type changes
    for change in diff.type_changes:
        new_sql_type = _udt_to_sql(change["new_type"])
        col = change["column"]

        # Boolean: map common truthy string values
        if new_sql_type == "BOOLEAN":
            using_clause = (
                f"CASE WHEN {col}::text IN ('1', 'true', 't', 'yes', 'y') THEN TRUE "
                f"ELSE FALSE END"
            )

        # Integer types: cast via NUMERIC first to safely handle float-formatted
        # strings like "1710.0" that would fail a direct ::BIGINT / ::INTEGER cast
        elif new_sql_type in ("SMALLINT", "INTEGER", "BIGINT"):
            using_clause = f"CAST(CAST({col} AS NUMERIC) AS {new_sql_type})"

        # Real / double: standard cast covers all string representations
        elif new_sql_type in ("REAL", "DOUBLE PRECISION"):
            using_clause = f"CAST({col} AS {new_sql_type})"

        # Date: values must already be ISO-formatted strings
        elif new_sql_type == "DATE":
            using_clause = f"CAST({col} AS DATE)"

        # Timestamp variants
        elif new_sql_type in ("TIMESTAMP", "TIMESTAMPTZ"):
            using_clause = f"CAST({col} AS {new_sql_type})"

        # UUID
        elif new_sql_type == "UUID":
            using_clause = f"CAST({col} AS UUID)"

        # All other types: generic cast
        else:
            using_clause = f"{col}::{new_sql_type}"

        # Drop any existing DEFAULT first — a default on the old type cannot be
        # automatically cast and will block the ALTER COLUMN TYPE even when the
        # data itself converts cleanly. Staging tables are constraint-free so we
        # never restore the default.
        statements.append(f'ALTER TABLE {change["table"]} ALTER COLUMN {col} DROP DEFAULT;')

        ddl = (
            f'ALTER TABLE {change["table"]} '
            f'ALTER COLUMN {col} TYPE {new_sql_type} '
            f'USING {using_clause};'
        )
        statements.append(ddl)
        logger.info(
            f"[SCHEMA] Will CHANGE TYPE: {change['table']}.{col} "
            f"{change['old_type']} → {change['new_type']} (USING {using_clause})"
        )

    # NOTE: Nullable constraint changes are intentionally skipped.
    # Staging tables on ServerB are constraint-free; NOT NULL / DROP NOT NULL
    # DDL is never emitted regardless of what the source schema declares.

    return statements


# ──────────────────────────────────────────────
# Applying DDL to ServerB
# ──────────────────────────────────────────────

def apply_ddl(dest_conn, statements: list[str], new_tables: list[str] = None) -> None:
    """Execute all DDL statements on the destination connection.

    Each statement is committed individually so that AccessExclusiveLocks
    acquired on partitioned table partitions are released immediately after
    each DDL. Accumulating all DDL in one transaction exhausts
    max_locks_per_transaction when tables have hundreds of partitions.

    For every CREATE TABLE statement, automatically calls
    proc_create_table_partitions_v3(<table_name>) immediately after
    (also committed individually), so partitions are provisioned before
    any data is loaded.
    """
    if not statements:
        logger.info("[SCHEMA] No DDL changes required. Schemas are in sync.")
        return

    new_tables_set = set(new_tables or [])
    applied = 0

    for stmt in statements:
        try:
            with dest_conn.cursor() as cur:
                cur.execute(stmt)
            dest_conn.commit()  # release partition locks immediately
            applied += 1
            logger.info(f"[SCHEMA] Applied: {stmt[:120].strip()}{'...' if len(stmt) > 120 else ''}")

            # For every new table, immediately provision its partitions
            if stmt.strip().upper().startswith("CREATE TABLE"):
                matched_table = next(
                    (t for t in new_tables_set if f' {t} ' in stmt or stmt.endswith(f' {t})')),
                    None
                )
                if matched_table:
                    with dest_conn.cursor() as cur2:
                        partition_call = f"CALL public.proc_create_table_partitions_v3('{matched_table}');"
                        cur2.execute(partition_call)
                    dest_conn.commit()  # commit partition creation separately too
                    logger.info(f"[SCHEMA] Partitions created for: {matched_table}")
                else:
                    logger.warning(
                        f"[SCHEMA] CREATE TABLE detected but could not resolve table name "
                        f"from statement: {stmt[:120]}"
                    )

        except psycopg2.Error as e:
            dest_conn.rollback()
            logger.exception(f"[SCHEMA] Failed to apply DDL:\n{stmt}\nError: {e}", exc_info=True)
            raise

    logger.info(f"[SCHEMA] {applied} DDL statement(s) applied to destination successfully.")


# ──────────────────────────────────────────────
# Reporting
# ──────────────────────────────────────────────

def log_diff_summary(diff: SchemaDiff) -> None:
    total = (
        len(diff.new_tables)
        + len(diff.new_columns)
        + len(diff.type_changes)
    )
    if total == 0:
        logger.info("[SCHEMA] Schema comparison complete — no differences found.")
        return

    logger.info(f"[SCHEMA] Differences found: {total} total")
    if diff.new_tables:
        logger.info(f"  New tables    : {len(diff.new_tables)} → {diff.new_tables}")
    if diff.new_columns:
        cols = [(c.table_name, c.column_name) for c in diff.new_columns]
        logger.info(f"  New columns   : {len(diff.new_columns)} → {cols}")
    if diff.type_changes:
        logger.info(f"  Type changes  : {len(diff.type_changes)}")
        for c in diff.type_changes:
            logger.info(f"    {c['table']}.{c['column']}: {c['old_type']} → {c['new_type']}")


# ──────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────

def run_schema_alignment(
    source_db_key: str = "server_a",
    dest_db_key: str = "server_b",
    dry_run: bool = False,
) -> SchemaDiff:
    """
    Compare schemas between ServerA and ServerB, then apply any required DDL
    to ServerB so it matches ServerA before ingestion runs.

    Parameters
    ----------
    source_db_key : str
        Key passed to connect_to_db.connect() for ServerA.
    dest_db_key : str
        Key passed to connect_to_db.connect() for ServerB.
    dry_run : bool
        If True, compute and log the diff but do NOT apply any DDL.

    Returns
    -------
    SchemaDiff
        The computed differences (useful for testing or upstream reporting).
    """
    logger.info("[SCHEMA] Starting schema alignment check …")

    # source_conn = connect_to_db.connect(source_db_key)[0]
    # dest_conn = connect_to_db.connect(dest_db_key)[0]

    source_conn = connect_to_db(source_db_key)[0]
    dest_conn = connect_to_db(dest_db_key)[0]

    try:
        logger.info("[SCHEMA] Fetching schema from ServerA (source) …")
        source_schema = fetch_schema(source_conn)

        logger.info("[SCHEMA] Fetching schema from ServerB (destination) …")
        dest_schema = fetch_schema(dest_conn, prefix="stg_")

        logger.info("[SCHEMA] Computing diff …")
        diff = compute_diff(source_schema, dest_schema)
        log_diff_summary(diff)

        statements = build_ddl_statements(diff, source_schema)

        if dry_run:
            logger.info("[SCHEMA] Dry-run mode — skipping DDL execution.")
            for stmt in statements:
                logger.info(f"[DRY-RUN] {stmt}")
        else:
            apply_ddl(dest_conn, statements, new_tables=diff.new_tables)

        logger.info("[SCHEMA] Schema alignment complete.")
        return diff

    finally:
        source_conn.close()
        dest_conn.close()


# ──────────────────────────────────────────────
# Standalone execution
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PostgreSQL cross-server schema alignment")
    parser.add_argument("--source", default="server_a", help="Source DB key (default: server_a)")
    parser.add_argument("--dest", default="server_b", help="Destination DB key (default: server_b)")
    parser.add_argument("--dry-run", action="store_true", help="Log changes without applying them")
    args = parser.parse_args()

    run_schema_alignment(
        source_db_key=args.source,
        dest_db_key=args.dest,
        dry_run=args.dry_run,
    )
