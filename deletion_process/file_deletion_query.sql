-- delete decrypted files
SELECT COUNT(decrypted_file_name)
--facility_id, decrypted_file_name, ingest_end_time, processed
FROM public.sync_file 
WHERE ingest_end_time <= CURRENT_DATE - INTERVAL '1' DAY
AND processed IN (2, -2) 
AND ingest_status_check = 'success' 
AND ingest_error_message = 'No errors' 
AND decrypted_file_name NOT IN (
SELECT REPLACE(file_name, '_decrypted.json', '.json') 
FROM file_deletion_log 
WHERE deletion_status_check = 'success' OR deletion_status_check = 'failed'
OR error_message = 'file not found') 
ORDER BY ingest_end_time DESC
LIMIT 100000;

-- delete encrypted files
SELECT facility_id, decrypted_file_name, ingest_end_time, processed
FROM public.sync_file 
WHERE create_date <= CURRENT_DATE - INTERVAL '1' DAY
AND processed IN (2, -2) 
AND ingest_status_check = 'success' 
AND ingest_error_message = 'No errors' 
AND decrypted_file_name NOT IN (
SELECT REPLACE(file_name, '_decrypted.json', '.json') 
FROM file_deletion_log 
WHERE deletion_status_check = 'success' OR deletion_status_check = 'failed'
OR error_message = 'file not found') 
ORDER BY create_date DESC
LIMIT 100000;