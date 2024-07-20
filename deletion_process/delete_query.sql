WITH CTE AS (
    SELECT file_name,
    ROW_NUMBER() OVER (PARTITION BY file_name ORDER BY deletion_start_time) AS row_num
FROM public.file_deletion_log 
where deletion_end_time is null and error_message is null
and deletion_start_time is not null
and deletion_status_check = 'processing'
limit 50)
DELETE FROM public.file_deletion_log
where deletion_end_time is null and error_message is null
and deletion_start_time is not null and deletion_status_check = 'processing';
