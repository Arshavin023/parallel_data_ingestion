"""
schema_alignment.py

Compares schema between ServerA (source) and ServerB (destination) and
automatically applies DDL changes to ServerB before ingestion runs.

Checks:
  - New tables in ServerA not present in ServerB  → CREATE TABLE
  - New columns in ServerA not present in ServerB → ALTER TABLE ... ADD COLUMN
  - Data type mismatches                            → ALTER TABLE ... ALTER COLUMN TYPE
"""

import psycopg2
from dataclasses import dataclass, field
from typing import Optional
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
    is_nullable: bool
    column_default: Optional[str]
    ordinal_position: int


@dataclass
class SchemaDiff:
    new_tables: list[str] = field(default_factory=list)
    new_columns: list[ColumnInfo] = field(default_factory=list)
    type_changes: list[dict] = field(default_factory=list)  # {table, column, old_type, new_type}
    nullable_changes: list[dict] = field(default_factory=list)


# ──────────────────────────────────────────────
# Schema fetching
# ──────────────────────────────────────────────

def fetch_schema(conn, prefix: str = "") -> dict[str, dict[str, ColumnInfo]]:
    schema: dict[str, dict[str, ColumnInfo]] = {}
    
    # Base source tables to monitor
    base_tables = [
        'hts_encounter', 'hts_ict_contact', 'hts_ict_encounter', 'hiv_adherence_preparation', 'prep_enrollment',
        'hiv_patient_transfer_in','pmtct_infant_pcr', 'prep_clinic','hiv_enrollment_commencement', 'hiv_initial_clinical_evaluation', 
        'prophylaxis_screening', 'prophylaxis_initiation', 'prophylaxis_interruptions', 'laboratory_sample',
        'prep_followup_visit', 'pep_followup_visit', 'pmtct_pregnancy_cycle', 'pmtct_anc','pmtct_infant_arv',
        'pmtct_enrollment', 'pmtct_delivery', 'pmtct_mother_visitation', 'pmtct_infant_information', 
        'pmtct_infant_visit', 'hiv_art_clinical', 'hiv_art_pharmacy', 'hiv_art_pharmacy_regimens', 
        'hiv_drug', 'hiv_eac', 'hiv_eac_out_come', 'hiv_eac_session', 'hiv_observation', 
        'hiv_ovc_linkage', 'hiv_patient_tracker', 'hiv_regimen', 'hiv_regimen_drug', 
        'hiv_regimen_resolver', 'hiv_regimen_type', 'hiv_status_tracker','prep_eligibility'
    ]
    
    # Append the prefix dynamically for query matching (e.g., searching for stg_hiv_drug on ServerB)
    target_tables = [f"{prefix}{t}" for t in base_tables] if prefix else base_tables

    DYNAMIC_SCHEMA_QUERY = """
        SELECT
            c.table_name,
            c.column_name,
            c.udt_name          AS data_type,
            (c.is_nullable = 'YES') AS is_nullable,
            c.column_default,
            c.ordinal_position
        FROM information_schema.columns c
        JOIN information_schema.tables t
            ON t.table_name = c.table_name
            AND t.table_schema = c.table_schema
        WHERE c.table_schema = 'public'
          AND t.table_type = 'BASE TABLE'
          AND t.table_name = ANY(%s)
        ORDER BY c.table_name, c.ordinal_position;
    """

    with conn.cursor() as cur:
        cur.execute(DYNAMIC_SCHEMA_QUERY, (target_tables,))
        for row in cur.fetchall():
            col = ColumnInfo(
                table_name=row[0],
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

    # Normalize destination keys to strip out "stg_" prefix for key-matching
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

# ──────────────────────────────────────────────
# DDL generation
# ──────────────────────────────────────────────

def _udt_to_sql(udt_name: str) -> str:
    mapping = {
        "int2": "SMALLINT", "int4": "INTEGER", "int8": "BIGINT",
        "float4": "REAL", "float8": "DOUBLE PRECISION", "numeric": "NUMERIC",
        "bool": "BOOLEAN", "bpchar": "CHAR", "varchar": "VARCHAR",
        "text": "TEXT", "date": "DATE", "timestamp": "TIMESTAMP",
        "timestamptz": "TIMESTAMPTZ", "uuid": "UUID", "json": "JSON",
        "jsonb": "JSONB", "bytea": "BYTEA",
    }
    return mapping.get(udt_name, udt_name.upper())


_STG_COLUMN_DEFS = (
    "    stg_batch_id   CHARACTER VARYING,\n"
    "    stg_load_time  TIMESTAMP WITHOUT TIME ZONE,\n"
    "    stg_file_name  CHARACTER VARYING,\n"
    "    stg_datim_id   CHARACTER VARYING"
)


def build_create_table_ddl(table_name: str, columns: dict[str, ColumnInfo]) -> str:
    col_defs = []
    for col in sorted(columns.values(), key=lambda c: c.ordinal_position):
        sql_type = _udt_to_sql(col.data_type)
        col_defs.append(f'    {col.column_name} {sql_type}')

    col_defs.append(_STG_COLUMN_DEFS)
    cols_sql = ",\n".join(col_defs)

    return f'CREATE TABLE IF NOT EXISTS {table_name} (\n{cols_sql}\n) PARTITION BY LIST (stg_datim_id);'


def build_ddl_statements(diff: SchemaDiff, source_schema: dict) -> list[str]:
    statements = []

    # 1. New tables
    for table_name in diff.new_tables:
        source_table = table_name.removeprefix("stg_")
        if source_table not in source_schema:
            continue
        ddl = build_create_table_ddl(table_name, source_schema[source_table])
        statements.append(ddl)
        logger.info(f"[SCHEMA] Will CREATE TABLE: {table_name}")

    # 2. New columns
    for col in diff.new_columns:
        sql_type = _udt_to_sql(col.data_type)
        ddl = f'ALTER TABLE {col.table_name} ADD COLUMN IF NOT EXISTS {col.column_name} {sql_type};'
        statements.append(ddl)
        logger.info(f"[SCHEMA] Will ADD COLUMN: {col.table_name}.{col.column_name} ({sql_type})")

    # 3. Type changes (Dynamic Safe Conversions)
    for change in diff.type_changes:
        new_sql_type = _udt_to_sql(change["new_type"])
        col = change["column"]

        # Dynamically treat conversion paths via text staging inside USING
        if new_sql_type == "BOOLEAN":
            using_clause = (
                f"CASE "
                f"WHEN LOWER({col}::text) IN ('1', 'true', 't', 'yes', 'y', '1.0') THEN TRUE "
                f"WHEN LOWER({col}::text) IN ('0', 'false', 'f', 'no', 'n', '0.0') THEN FALSE "
                f"ELSE NULL "
                f"END"
            )
        elif new_sql_type in ("SMALLINT", "INTEGER", "BIGINT"):
            using_clause = f"NULLIF(REGEXP_REPLACE({col}::text, '[^0-9.-]', '', 'g'), '')::numeric::{new_sql_type}"
        elif new_sql_type in ("REAL", "DOUBLE PRECISION", "NUMERIC"):
            using_clause = f"NULLIF(REGEXP_REPLACE({col}::text, '[^0-9.-]', '', 'g'), '')::numeric"
        elif new_sql_type == "DATE":
            using_clause = f"CAST({col}::text AS DATE)"
        elif new_sql_type in ("TIMESTAMP", "TIMESTAMPTZ"):
            using_clause = f"CAST({col}::text AS {new_sql_type})"
        else:
            using_clause = f"{col}::{new_sql_type}"

        # Drop defaults before changing column type
        statements.append(f'ALTER TABLE {change["table"]} ALTER COLUMN {col} DROP DEFAULT;')
        statements.append(f'ALTER TABLE {change["table"]} ALTER COLUMN {col} TYPE {new_sql_type} USING {using_clause};')
        
        logger.info(f"[SCHEMA] Will CHANGE TYPE: {change['table']}.{col} ({change['old_type']} -> {new_sql_type})")

    return statements

# ──────────────────────────────────────────────
# Applying DDL and Core Logic Execution
# ──────────────────────────────────────────────

def apply_ddl(dest_conn, statements: list[str], new_tables: list[str] = None) -> None:
    if not statements:
        logger.info("[SCHEMA] No DDL changes required. Schemas are in sync.")
        return

    new_tables_set = set(new_tables or [])
    applied = 0

    for stmt in statements:
        try:
            with dest_conn.cursor() as cur:
                cur.execute(stmt)
            dest_conn.commit()
            applied += 1
            logger.info(f"[SCHEMA] Applied: {stmt[:120].strip()}...")

            if stmt.strip().upper().startswith("CREATE TABLE"):
                matched_table = next((t for t in new_tables_set if f' {t} ' in stmt or stmt.endswith(f' {t})')), None)
                if matched_table:
                    with dest_conn.cursor() as cur2:
                        cur2.execute(f"CALL public.proc_create_table_partitions_v3('{matched_table}');")
                    dest_conn.commit()
                    logger.info(f"[SCHEMA] Partitions created for: {matched_table}")
        except psycopg2.Error as e:
            dest_conn.rollback()
            logger.exception(f"[SCHEMA] Failed to apply DDL:\n{stmt}\nError: {e}")
            raise

    logger.info(f"[SCHEMA] {applied} DDL statement(s) applied successfully.")


def log_diff_summary(diff: SchemaDiff) -> None:
    total = len(diff.new_tables) + len(diff.new_columns) + len(diff.type_changes)
    if total == 0:
        logger.info("[SCHEMA] Schema comparison complete — no differences found.")
        return
    logger.info(f"[SCHEMA] Differences found: {total} total")


def run_schema_alignment(source_db_key: str = "server_a", dest_db_key: str = "server_b", dry_run: bool = False) -> SchemaDiff:
    logger.info("[SCHEMA] Starting schema alignment check …")
    source_conn = connect_to_db(source_db_key)[0]
    dest_conn = connect_to_db(dest_db_key)[0]

    try:
        logger.info("[SCHEMA] Fetching schema from ServerA (source) …")
        source_schema = fetch_schema(source_conn, prefix="")

        logger.info("[SCHEMA] Fetching schema from ServerB (destination) …")
        dest_schema = fetch_schema(dest_conn, prefix="stg_")

        logger.info("[SCHEMA] Computing diff …")
        diff = compute_diff(source_schema, dest_schema)
        log_diff_summary(diff)

        statements = build_ddl_statements(diff, source_schema)

        if dry_run:
            for stmt in statements:
                logger.info(f"[DRY-RUN] {stmt}")
        else:
            apply_ddl(dest_conn, statements, new_tables=diff.new_tables)

        return diff
    finally:
        source_conn.close()
        dest_conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="server_a")
    parser.add_argument("--dest", default="server_b")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run_schema_alignment(source_db_key=args.source, dest_db_key=args.dest, dry_run=args.dry_run)
