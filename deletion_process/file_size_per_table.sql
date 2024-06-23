WITH table_size_info AS (
    SELECT
        table_name,pg_total_relation_size(quote_ident(table_name)) / 1048576.0 AS total_size_megabytes
    FROM information_schema.tables
    WHERE table_schema = 'public'
)
--UPDATE stg_records_deletion_log srdl
--SET table_size_after_deletion = tsi.total_size_megabytes
--FROM table_size_info tsi
--WHERE srdl.table_name = tsi.table_name;
SELECT tsi.table_name,tsi.total_size_megabytes,srdl.deleted_records_count,srdl.start_time,srdl.end_time,
srdl.table_size_before_deletion,srdl.table_size_after_deletion
FROM table_size_info tsi LEFT JOIN stg_records_deletion_log srdl on tsi.table_name=srdl.table_name
WHERE total_size_megabytes > 200 AND tsi.table_name ILIKE 'stg_%'
order by total_size_megabytes desc;
