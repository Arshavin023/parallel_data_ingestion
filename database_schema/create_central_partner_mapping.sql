CREATE TABLE IF NOT EXISTS public.central_partner_mapping
(
    id bigint,
    facility_id bigint NOT NULL,
    datim_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
    facility_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    facility_state character varying(255) COLLATE pg_catalog."default" NOT NULL,
    facility_lga character varying(255) COLLATE pg_catalog."default" NOT NULL,
    ip_code bigint NOT NULL,
    ip_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    patient_count integer,
    archived integer DEFAULT 0,
    lga_id character varying COLLATE pg_catalog."default",
    is_run boolean DEFAULT false,
    orgunitid character varying COLLATE pg_catalog."default",
    attributeuid character varying COLLATE pg_catalog."default",
    CONSTRAINT central_partner_mapping_pkey PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.central_partner_mapping
    OWNER to lamisplus;
