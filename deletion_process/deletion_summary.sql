SELECT count(*)
FROM public.sync_file 
WHERE ingest_end_time <= CURRENT_DATE + interval '1' day
AND processed IN (2) --OR ingest_error_message ilike '%invalid dates%'
AND decrypted_file_name NOT IN (
SELECT REPLACE(file_name, '_decrypted.json', '.json') 
FROM file_deletion_log 
WHERE deletion_status_check in ('success','failed'))
--OR error_message ilike 'file not found%')
ORDER BY ingest_end_time ASC
LIMIT 50

select * from file_deletion_log
--delete from file_deletion_log
where deletion_end_time is null and error_message is null
and deletion_start_time is not null and deletion_status_check = 'processing'
limit 4


SELECT count(*)
FROM public.sync_file 
WHERE create_date <= CURRENT_DATE - INTERVAL '1' DAY
AND processed IN (2,-2) 
AND decrypted_file_name NOT IN (
SELECT REPLACE(file_name, '_decrypted.json', '.json') 
FROM file_deletion_log 
WHERE deletion_status_check in ('success','failed')
--OR error_message ilike 'file not found%')
	)
ORDER BY ingest_end_time ASC

SELECT *
FROM file_deletion_log 
where deletion_end_time is not null and deletion_status_check='success'
and deletion_end_time >= CURRENT_DATE -interval '1' day
order by deletion_end_time desc
limit 49

SELECT file_name
FROM public.file_deletion_log                         
WHERE deletion_status_check in ('processing')
ORDER BY deletion_end_time ASC
LIMIT 50
