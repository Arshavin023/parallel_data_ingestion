SELECT table_name,pg_size_pretty(pg_total_relation_size(quote_ident(table_name))::bigint) AS total_size_gb
--pg_total_relation_size(quote_ident(table_name))
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name ILIKE 'stg_%'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC