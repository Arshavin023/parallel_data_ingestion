select * from stg_monitoring limit 3;
SELECT table_name, table_schema, table_name,pg_size_pretty(pg_total_relation_size(table_schema || '.' || table_name)::bigint) AS total_size
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name ILIKE 'stg_%' and table_name NOT ILIKE '%_bad_dates'
ORDER BY pg_total_relation_size(quote_ident(table_name)) desc;
