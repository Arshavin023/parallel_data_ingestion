CREATE OR REPLACE PROCEDURE proc_delete_stg_records(table_name character varying)
AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    deleted_count bigint;
	table_size_before_deletion bigint;
	table_size_after_deletion bigint;
BEGIN
    -- Get the current start time
    SELECT TIMEOFDAY() INTO start_time;
    
	--Get size of table in megabytes before deletion
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
	
	-- Get the current end time
    SELECT TIMEOFDAY() INTO end_time;
	
    -- Log or perform any other operations if needed
    INSERT INTO stg_records_deletion_log (table_name, deleted_records_count, start_time, end_time,
											table_size_before_deletion,table_size_after_deletion) 
    VALUES (table_name, deleted_count, start_time, end_time,table_size_before_deletion,table_size_after_deletion);
    
END $$ LANGUAGE plpgsql;
