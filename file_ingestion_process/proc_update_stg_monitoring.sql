-- PROCEDURE: public.update_stg_monitoring()

-- DROP PROCEDURE IF EXISTS public.update_stg_monitoring();

CREATE OR REPLACE PROCEDURE public.update_stg_monitoring(
	)
LANGUAGE 'plpgsql'
AS $BODY$
BEGIN

INSERT INTO public.stg_monitoring(
    datim_id, batch_id, file_name, table_name, load_time, json_rec_count, stg_rec_count, processed
)
SELECT
    datim_id, batch_id, ingest_file_name AS file_name, ingest_table_name AS table_name, load_time, json_rec_count, stg_rec_count, processed
FROM dblink(
    'db_link_filedb',
    'SELECT facility_id AS datim_id,
            REVERSE(SPLIT_PART(REVERSE(ingest_file_name), ''_'', 2)) AS batch_id,
            ingest_file_name,
            ingest_table_name,
            ingest_end_time AS load_time,
            json_rec_count,
            json_rec_count AS stg_rec_count,
            ''N'' AS processed
     FROM sync_file
     WHERE json_rec_count > 0 AND create_date >= ''2024-07-15''
') AS result(
    datim_id character varying,
    batch_id text,
    ingest_file_name character varying,
    ingest_table_name character varying,
    load_time timestamp,
    json_rec_count bigint,
    stg_rec_count bigint,
    processed text
)
ON CONFLICT (datim_id, batch_id, file_name, table_name)
DO NOTHING;

END;
$BODY$;
ALTER PROCEDURE public.update_stg_monitoring()
    OWNER TO lamisplus;
