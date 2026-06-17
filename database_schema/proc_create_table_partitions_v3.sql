-- PROCEDURE: public.proc_create_table_partitions_v3(character varying)

-- DROP PROCEDURE IF EXISTS public.proc_create_table_partitions_v3(character varying);

CREATE OR REPLACE PROCEDURE public.proc_create_table_partitions_v3(
	IN stg_table_name character varying)
LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    inputs text[];
    input text;
	partition_name text;
	partition_name2 text;
	
BEGIN
    -- Populate the array with values from the existing table
    SELECT array_agg(datim_id)
	INTO inputs
	FROM central_partner_mapping;

    -- Loop through each input value and execute the dynamic query
    FOREACH input IN ARRAY inputs
    LOOP
		
		partition_name := CONCAT(REPLACE(stg_table_name,'stg_',''),'_',input);
		EXECUTE FORMAT('CREATE TABLE IF NOT EXISTS public.%I 
					   PARTITION OF %s
					   FOR VALUES IN (%L)',
					  partition_name,stg_table_name,input);
	RAISE NOTICE 'successfully created %', partition_name;

    END LOOP;
END;
$BODY$;
ALTER PROCEDURE public.proc_create_table_partitions_v3(character varying)
    OWNER TO lamisplus;

-- CALL public.proc_create_table_partitions_v3('stg_patient_person');
