-- Table: public.batch_facility_id_logs
DROP TABLE IF EXISTS public.batch_facility_id_logs;
DROP SEQUENCE IF EXISTS batch_facility_id_logs_seq;
CREATE SEQUENCE IF NOT EXISTS batch_facility_id_logs_seq;

CREATE TABLE IF NOT EXISTS public.batch_facility_id_logs
(
    id bigint NOT NULL DEFAULT nextval('batch_facility_id_logs_seq'::regclass),
    facility_id character varying(255) COLLATE pg_catalog."default",
    facility_id_count bigint,
    status character varying(255) COLLATE pg_catalog."default",
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    error_message character varying(2000000) COLLATE pg_catalog."default",
    CONSTRAINT batch_facility_id_logs_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.batch_facility_id_logs
    OWNER to lamisplus;