-- PROCEDURE: public.proc_update_sync_queue_tracker_refresh()

-- DROP PROCEDURE IF EXISTS public.proc_update_sync_queue_tracker_refresh();

CREATE OR REPLACE PROCEDURE public.proc_update_sync_queue_tracker_refresh(
	)
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE start_time TIMESTAMP;
DECLARE last_load_end_time TIMESTAMP;
DECLARE end_time TIMESTAMP;

BEGIN

SELECT TIMEOFDAY() INTO start_time;

update public.sync_queue_tracker t2
set status='Processed'
FROM (SELECT * FROM dblink('db_link_filedb',
'select file_name, ingest_error_message error_message, ''Error while processing'' status
from sync_file 
WHERE processed=2
AND create_date>=''2015-07-15''
ORDER BY ingest_end_time DESC
') AS sm(file_name character varying,error_message character varying, status text))t1
WHERE t2.file_name=t1.file_name
AND t2.status != 'Processed';
	
SELECT TIMEOFDAY() INTO end_time;

INSERT INTO public.update_sync_queue_tracker_monitoring(table_name,start_time,load_end_time)
VALUES('update_sync_queue_tracker',start_time, end_time);
		 
END 
$BODY$;
ALTER PROCEDURE public.proc_update_sync_queue_tracker_refresh()
    OWNER TO lamisplus;
