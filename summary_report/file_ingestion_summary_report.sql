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
and not (decrypted_file_name ilike '%dsd_devolvement%' or decrypted_file_name ilike '%hiv_art_clinical%')
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
and (decrypted_file_name ilike '%dsd_devolvement%' or decrypted_file_name ilike '%hiv_art_clinical%');

--Check for dict data type error in hiv_art_clinical and dsd_devolvement
select decrypted_file_name,ingest_table_name,ingest_start_time,ingest_end_time,ingest_error_message
from public.sync_file
--,processed,
--update public.sync_file set processed = 1
where processed=2 and ingest_end_time is not null and
--and ingest_error_message ilike '%adapt type ''dict''%'
decrypted_file_name ilike '%biometric%'
--and 
--and (decrypted_file_name ilike '%dsd_devolvement%' or decrypted_file_name ilike '%hiv_art_clinical%')
order by ingest_end_time desc
limit 20;
e_name ilike '%hiv_art_clinical%')
order by create_date desc
limit 5

-- check for bad dates in IPs, facilities, etc
select cpm.ip_name,cpm.facility_name,sf.decrypted_file_name,ingest_end_time,sf.ingest_error_message
from sync_file sf
left join central_partner_mapping cpm on sf.facility_id=cpm.datim_id
where processed = -2 
--and cpm.ip_name in ('ACE-6')
--and ingest_status_check = 'failed'
and create_date >= '2024-06-28' 
and ingest_error_message ilike '%invalid dates%'
order by ingest_end_time desc,decrypted_file_name;