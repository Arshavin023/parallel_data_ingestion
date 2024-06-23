SELECT count(id) Total_Files,
SUM(CASE WHEN processed =2 THEN 1 ELSE 0 END) processed_count,
SUM(CASE WHEN processed =0 THEN 1 ELSE 0 END) just_uploaded,
SUM(CASE WHEN processed =-1 THEN 1 ELSE 0 END) decryption_queue,
SUM(CASE WHEN processed =1 THEN 1 ELSE 0 END) decrypted_complete,
SUM(CASE WHEN processed =-2 AND ingest_status_check is null THEN 1 ELSE 0 END) real_decryption_fails,
SUM(CASE WHEN processed =-2 AND ingest_status_check is not null THEN 1 ELSE 0 END) ingestion_fails,
SUM(CASE WHEN processed =-2 THEN 1 ELSE 0 END) fails, CURRENT_TIMESTAMP check_data
FROM public.sync_file
where create_date >= '2024-03-21'
and decrypted_file_name not like '%dsd_devolvement%'
union all
SELECT count(id) Total_Files,
SUM(CASE WHEN processed =2 THEN 1 ELSE 0 END) processed_count,
SUM(CASE WHEN processed =0 THEN 1 ELSE 0 END) just_uploaded,
SUM(CASE WHEN processed =-1 THEN 1 ELSE 0 END) decryption_queue,
SUM(CASE WHEN processed =1 THEN 1 ELSE 0 END) decrypted_complete,
SUM(CASE WHEN processed =-2 AND ingest_status_check is null THEN 1 ELSE 0 END) real_decryption_fails,
SUM(CASE WHEN processed =-2 AND ingest_status_check is not null THEN 1 ELSE 0 END) ingestion_fails,
SUM(CASE WHEN processed =-2 THEN 1 ELSE 0 END) fails, CURRENT_TIMESTAMP check_data
FROM public.sync_file
where create_date >= '2024-03-21'
and decrypted_file_name like '%dsd_devolvement%';





