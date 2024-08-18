update public.sync_queue_tracker t2
set status='Procesed'
FROM (SELECT * FROM temp_sync_queue_tracker p)t1
WHERE t2.file_name=t1.file_name
AND t1.processed=2

--SELECT t1.file_name t1_filename, t2.file_name t2_filename, t1.status t1_status, 
--t2.status t2_status, t1.error_message t1_error, t2.error_message t2_error
--FROM (SELECT * FROM temp_sync_queue_tracker p)t1, public.sync_queue_tracker t2
--WHERE t2.file_name=t1.file_name 
--AND t2.status!='Error while processing' 