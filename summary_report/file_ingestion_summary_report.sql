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

--check newly added columns;
select *
--decrypted_file_name,ingest_start_time,ingest_end_time, 
from public.sync_file
--update public.sync_file
--set processed = 1
where processed=-2 and ingest_start_time >= '2024-06-28'
and ingest_error_message not ilike '%please review, fix and reupload%'
--order by ingest_end_time desc
limit 10
;


--check ProgrammingError - (psycopg2.ProgrammingError) can't adapt type 'dict' error;
select 
--distinct ingest_table_name,ingest_error_message
decrypted_file_name,processed,ingest_start_time,ingest_end_time,ingest_error_message
from public.sync_file
--update public.sync_file
--set processed = 1
where processed=-2 
--and ingest_start_time >= '2024-06-28'
and ingest_error_message ilike '%ProgrammingError - (psycopg2.ProgrammingError)%'
and ingest_table_name in ('stg_hiv_art_clinical','stg_dsd_devolvement')
order by ingest_end_time desc
limit 20;

select sf.facility_id,cpm.facility_name,sf.decrypted_file_name,sf.processed,
sf.ingest_error_message,sf.ingest_end_time
from sync_file sf
left join central_partner_mapping cpm on sf.facility_id=cpm.datim_id
where processed = -2
--and ingest_status_check = 'failed'
and 
ingest_end_time >= '2024-06-28' 
and ingest_error_message ilike '%please review, fix and reupload%'
--and file_name ilike '%dsd_devolvement%'
--and ingest_error_message ilike '%has invalid dates %'
order by ingest_end_time desc,decrypted_file_name;

--check for errors in hiv_art_clinical and dsd_devolvement;
select distinct decrypted_file_name,ingest_table_name,processed,ingest_error_message,ingest_end_time
--decrypted_file_name,ingest_start_time,ingest_end_time, 
from public.sync_file 
--update public.sync_file
--set processed = 1
where 
--create_date >= '2024-06-30' and
--ingest_table_name ilike '%prep_clinic%' and
processed = -2
and ingest_error_message not ilike '%please review, fix and reupload%'
and ingest_error_message 
not ilike '%ProgrammingError - (UndefinedColumn) column "facilty_id" of relation "mhpss_screening" does not exist%'
and ingest_error_message 
not ilike '%Given final block not properly padded. Such issues can arise if a bad key is used during decryption.%'
and ingest_error_message 
not ilike '%UnicodeDecodeError - File is corrupted and unreadable, kindly regenerate and re-upload%'
and NOT (decrypted_file_name ilike 'hiv_art_clinical%' or decrypted_file_name ilike 'dsd_devolvement%')
and ingest_error_message not ilike '%localhost%'