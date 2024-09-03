<<<<<<< HEAD
SELECT table_schema, table_name,pg_size_pretty(pg_total_relation_size(table_schema || '.' || table_name)::bigint) AS total_size
FROM information_schema.tables
WHERE table_schema in ('public','pharmacy','pmtct_hts','maternal_cohort','hackathon','clinic',
					   'mobile','hts_prep_datamart','expanded_hts_prep','expanded_radet')
and table_name not ilike '%_q3%'
ORDER BY pg_total_relation_size(table_schema || '.' || table_name) DESC;


SELECT table_schema, table_name,
    pg_size_pretty(pg_total_relation_size(table_schema || '.' || table_name)::bigint) AS total_size
FROM information_schema.tables
WHERE table_schema in ('pharmacy','public')
AND table_name IN ('temp_ods_hiv_status_tracker','temp_ods_laboratory_result',
				   'temp_ods_patient_visit','temp_ods_hiv_art_pharmacy_regimens',
				   'ods_biometric','cte_pharmacy_result','dedupprep_stg_hts_client',
				   'ods_patient_visit')
ORDER BY pg_total_relation_size(table_schema || '.' || table_name) DESC;


select * from public.stg_records_deletion_log
order by start_time desc limit 100;

select CURRENT_DATE - INTERVAL '21' DAY

select * from stg_biometric
WHERE stg_load_time <= CURRENT_DATE - INTERVAL '45' DAY
limit 3
=======
select * from stg_monitoring limit 3;
SELECT table_name, table_schema, table_name,pg_size_pretty(pg_total_relation_size(table_schema || '.' || table_name)::bigint) AS total_size
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name ILIKE 'stg_%' and table_name NOT ILIKE '%_bad_dates'
ORDER BY pg_total_relation_size(quote_ident(table_name)) desc;
>>>>>>> test
