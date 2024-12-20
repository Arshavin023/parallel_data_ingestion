WITH extracted_errors AS (
	SELECT file_name, 
	TRIM(CONCAT(substring(ingest_error_message FROM '^[^.]+'),'.json')) AS extracted_file_name,
	ingest_error_message AS new_error_message,
row_number() over (partition by file_name order by ingest_end_time) row
FROM sync_file
WHERE file_name IN (SELECT file_name FROM sync_file
					WHERE file_name NOT LIKE '%' || 
    regexp_replace(ingest_error_message, '.*?([a-zA-Z0-9_]+\.json).*', '\1') || '%'
	AND ingest_error_message != 'No errors')
AND ingest_error_message != 'Given final block not properly padded. Such issues can arise if a bad key is used during decryption.'
AND ingest_error_message != 'No space left on device'
AND ingest_error_message != 'error while ingesting, kindly reupload'
AND ingest_error_message NOT ILIKE '%is empty'
AND ingest_error_message != 'No errors'
)
UPDATE sync_file sf
SET ingest_error_message = 'No errors'
FROM extracted_errors ee
WHERE sf.file_name = ee.file_name AND sf.ingest_error_message != 'No errors';


UPDATE sync_file
SET processed=2, ingest_status_check='success'
WHERE processed=-2
AND ingest_error_message='No errors'
AND ingest_status_check='failed';

UPDATE sync_file
SET ingest_file_name= REPLACE(file_name,'.json','_decrypted.json'), ingest_status_check='success'
WHERE processed=-2
AND ingest_error_message='No errors'
AND ingest_status_check='failed';

UPDATE sync_file
SET ingest_file_name= REPLACE(file_name,'.json','_decrypted.json') 
WHERE file_name != REPLACE(ingest_file_name,'_decrypted.json','.json')
;

SELECT count(*)
FROM sync_file
WHERE file_name != REPLACE(ingest_file_name,'_decrypted.json','.json');

SELECT 
    file_name,
    'stg_' || LEFT(file_name, POSITION('_' || SUBSTRING(file_name, '[0-9]') 
									   IN file_name) - 1) AS table_name
FROM sync_file LIMIT 100;