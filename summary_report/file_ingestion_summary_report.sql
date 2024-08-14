SELECT count(id) Total_Files,
SUM(CASE WHEN processed =2 THEN 1 ELSE 0 END) processed_count,
SUM(CASE WHEN processed =0 THEN 1 ELSE 0 END) just_uploaded,
SUM(CASE WHEN processed =-1 THEN 1 ELSE 0 END) decryption_queue,
SUM(CASE WHEN processed =1 THEN 1 ELSE 0 END) decrypted_complete,
SUM(CASE WHEN processed =-2 AND ingest_status_check is null THEN 1 ELSE 0 END) real_decryption_fails,
SUM(CASE WHEN processed =-2 AND ingest_status_check is not null THEN 1 ELSE 0 END) ingestion_fails,
SUM(CASE WHEN processed =-2 THEN 1 ELSE 0 END) fails, CURRENT_TIMESTAMP check_data
FROM public.sync_file
where modified_date >= '2024-06-30'
and not (decrypted_file_name ilike '%dsd_devolvement%' or decrypted_file_name ilike '%hiv_art_clinical%' or
decrypted_file_name ilike 'mhpss_confirmation%')
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
where modified_date >= '2024-06-30'
and (decrypted_file_name ilike '%dsd_devolvement%' or decrypted_file_name ilike '%hiv_art_clinical%'
	or decrypted_file_name ilike 'mhpss_confirmation%');

--Check for dict data type error in hiv_art_clinical and dsd_devolvement
select *
from public.sync_file 
where 
processed=2 and create_date >= '2024-06-30' 
order by ingest_end_time desc limit 50
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
select cpm.ip_name,cpm.facility_name,sf.create_date,sf.modified_date,sf.decrypted_file_name,ingest_table_name,processed,
sf.ingest_start_time,sf.ingest_end_time,sf.facility_id,sf.json_rec_count, sf.ingest_error_message
from sync_file sf left join central_partner_mapping cpm on sf.facility_id=cpm.datim_id
--delete from sync_file
where processed = -2 and modified_date >= '2024-07-20'
--and cpm.ip_name in ('ACE-1')
--and
--update sync_file set processed=1 where processed=-2 --and modified_date >= '2024-07-23'
--and file_name ilike '%laboratory_order_0_20240723170117.json%'
--and ingest_error_message ilike '%ValueError%' 
--and ingest_error_message ilike '%Bad date records were filtered%'
order by ingest_end_time desc,decrypted_file_name
limit 20;

SELECT count(*)
FROM sync_file 
--update sync_file set processed=1
--delete from sync_file
WHERE processed = 1 --and
--modified_date >= '2024-07-20' 
--and file_name ilike '%hiv_art_clinical_11_20240723010334.json%'
and ingest_start_time is null AND ingest_error_message is null
AND (decrypted_file_name ilike 'hiv_art_clinical%' or decrypted_file_name 
ilike 'dsd_devolvement%')
ORDER BY modified_date DESC


--SELECT decrypted_file_name, ingest_error_message,
update sync_file
set ingest_error_message=REPLACE(ingest_error_message,' successfully ingested',
       CONCAT(' ',json_rec_count, ' records successfully ingested')),
		processed=-2
--SELECT decrypted_file_name, ingest_error_message from sync_file
WHERE processed = 2 and ingest_start_time >= '2024-07-31'  
and ingest_error_message ilike '% ingested'
and decrypted_file_name in ('hiv_art_pharmacy_15_20240731125137.json')

select processed,replace(file_name,'.json','_decrypted.json')
						 json_rec_count,ingest_error_message,ingest_start_time,ingest_end_time
from sync_file
WHERE processed = 2 and ingest_start_time >= '2024-06-01' 
--and ingest_error_message ilike '% ingested' 
AND facility_id in ('f0J277xHATh')
--and decrypted_file_name in ('hiv_enrollment_0_20240729165118.json')
--and ingest_end_time is null 
ORDER BY ingest_end_time DESC
LIMIT 100


select * 
from sync_file
WHERE processed =-2 and ingest_start_time = '2024-08-' 
and ingest_error_message ilike '%ingested' 
--AND facility_id in ('f0J277xHATh')
and decrypted_file_name ilike 'hiv_art_clinical%'
--and ingest_end_time is null 
ORDER BY ingest_end_time DESC