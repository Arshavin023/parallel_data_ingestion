drop table if exists temp_sync_queue_tracker;
create table temp_sync_queue_tracker as
select decrypted_file_name file_name,ingest_error_message error_message,
'Error while processing' status
from sync_file 
WHERE processed=2 and create_date >= '2024-08-01'
order by create_date asc