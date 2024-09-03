<<<<<<< HEAD
CREATE OR REPLACE PROCEDURE proc_delete_stg_records(table_name character varying)
AS $$
=======
-- PROCEDURE: public.proc_delete_stg_records(character varying)

-- DROP PROCEDURE IF EXISTS public.proc_delete_stg_records(character varying);

CREATE OR REPLACE PROCEDURE public.proc_delete_stg_records(
	IN table_name character varying)
LANGUAGE 'plpgsql'
AS $BODY$
>>>>>>> test
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    deleted_count bigint;
<<<<<<< HEAD
	table_size_before_deletion bigint;
	table_size_after_deletion bigint;
=======
	size_before_deletion text;
	size_after_deletion text;
>>>>>>> test
BEGIN
    -- Get the current start time
    SELECT TIMEOFDAY() INTO start_time;
    
	--Get size of table in megabytes before deletion
<<<<<<< HEAD
	EXECUTE format ('SELECT pg_total_relation_size(quote_ident(table_name))/1048576
					FROM information_schema.tables WHERE table_schema = ''public'' AND table_name = ''%I''', table_name)
	INTO table_size_before_deletion;
				
    -- Execute a dynamic SQL to get the count of records to be deleted
    EXECUTE format('SELECT COUNT(*) FROM %I WHERE stg_load_time <= CURRENT_DATE - INTERVAL ''30'' DAY', table_name)
    INTO deleted_count;
    
    -- Execute dynamic SQL to delete records from the specified table
    EXECUTE format('DELETE FROM %I WHERE stg_load_time <= CURRENT_DATE - INTERVAL ''30'' DAY', table_name);
    
	-- Get size of table in megabytes after deletion
	EXECUTE format ('SELECT pg_total_relation_size(quote_ident(table_name))/1048576
					FROM information_schema.tables WHERE table_schema = ''public'' AND table_name = ''%I''', table_name)
	INTO table_size_after_deletion;
=======
	EXECUTE format ('SELECT pg_size_pretty(pg_total_relation_size(table_schema || ''.'' || table_name)::bigint)
                FROM information_schema.tables WHERE table_schema = ''public'' AND table_name = ''%s''',
                 table_name)
	INTO size_before_deletion;
	
				
    -- Execute a dynamic SQL to get the count of records to be deleted
    EXECUTE format('select count(stg_batch_id)
				   FROM %I WHERE stg_file_name IN (
				   select DISTINCT file_name FROM stg_monitoring
				   where processed=''Y'' and table_name = ''%s'')
				   ',table_name,table_name)
    INTO deleted_count;
    
	-- Execute dynamic SQL to delete records from the stg tables
	EXECUTE format('DELETE FROM %I WHERE stg_file_name IN (
				   select DISTINCT file_name FROM stg_monitoring 
					where processed=''Y'' and table_name = ''%s'')',table_name,table_name);
					
	-- Execute dynamic SQL to update stg_monitoring for records deleted from the stg tables
	EXECUTE format('UPDATE stg_monitoring
					SET stg_deleted = ''Y''
					WHERE file_name IN (
						SELECT DISTINCT file_name
						FROM stg_monitoring
						WHERE processed = ''Y'' and table_name = ''%s'')',table_name);
    
	--Get size of table in megabytes before deletion
	EXECUTE format ('SELECT pg_size_pretty(pg_total_relation_size(table_schema || ''.'' || table_name)::bigint)
                FROM information_schema.tables WHERE table_schema = ''public'' AND table_name = ''%s''',
                'public', table_name, table_name)
	INTO size_after_deletion;
>>>>>>> test
	
	-- Get the current end time
    SELECT TIMEOFDAY() INTO end_time;
	
    -- Log or perform any other operations if needed
    INSERT INTO stg_records_deletion_log (table_name, deleted_records_count, start_time, end_time,
<<<<<<< HEAD
											table_size_before_deletion,table_size_after_deletion) 
    VALUES (table_name, deleted_count, start_time, end_time,table_size_before_deletion,table_size_after_deletion);
    
END 

$$ LANGUAGE plpgsql;
=======
											size_before_deletion,size_after_deletion) 
    VALUES (table_name, deleted_count, start_time, end_time,size_before_deletion,size_after_deletion);
    
END 

$BODY$;
ALTER PROCEDURE public.proc_delete_stg_records(character varying)
    OWNER TO lamisplus;
>>>>>>> test
