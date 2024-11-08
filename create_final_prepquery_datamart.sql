-- Table: hts_prep_datamart.final_prepquery_datamart

DROP TABLE IF EXISTS hts_prep_datamart.final_prepquery_datamart;

CREATE TABLE IF NOT EXISTS hts_prep_datamart.final_prepquery_datamart
(
    period text COLLATE pg_catalog."default",
    personuuid character varying COLLATE pg_catalog."default",
    id bigint,
    uuid character varying COLLATE pg_catalog."default",
    hospitalnumber character varying COLLATE pg_catalog."default",
    surname text COLLATE pg_catalog."default",
    firstname text COLLATE pg_catalog."default",
    hivenrollmentdate date,
    age numeric,
    othername character varying COLLATE pg_catalog."default",
    sex character varying COLLATE pg_catalog."default",
    dateofbirth date,
    dateofregistration date,
    maritalstatus text COLLATE pg_catalog."default",
    education text COLLATE pg_catalog."default",
    occupation text COLLATE pg_catalog."default",
    facilityname character varying COLLATE pg_catalog."default",
    lga character varying COLLATE pg_catalog."default",
    state character varying COLLATE pg_catalog."default",
    datimid character varying(255) COLLATE pg_catalog."default",
    residentialstate character varying COLLATE pg_catalog."default",
    residentiallga character varying COLLATE pg_catalog."default",
    phone text COLLATE pg_catalog."default",
    address text COLLATE pg_catalog."default",
    baselineregimen character varying COLLATE pg_catalog."default",
    preptype character varying COLLATE pg_catalog."default",
    prepdistributionsetting character varying COLLATE pg_catalog."default",
    baselinesystolicbp double precision,
    baselinediastolicbp double precision,
    baselineweight double precision,
    baselineheight double precision,
    targetgroup character varying COLLATE pg_catalog."default",
    prepcommencementdate date,
    baselineurinalysis text COLLATE pg_catalog."default",
    baselineurinalysisdate date,
    baselinecreatinine text COLLATE pg_catalog."default",
    baselinecreatininetestdate date,
    baselinealt text COLLATE pg_catalog."default",
    baselinehbsag text COLLATE pg_catalog."default",
    baselinehbpcv text COLLATE pg_catalog."default",
    baselinewbc text COLLATE pg_catalog."default",
    currentalt text COLLATE pg_catalog."default",
    currentaltdate date,
    currenthbsag text COLLATE pg_catalog."default",
    currenthbsagdate date,
    currenthbpcv text COLLATE pg_catalog."default",
    currenthbpcvdate date,
    currentwbc text COLLATE pg_catalog."default",
    currentwbcdate date,
    baselinehepatitisb text COLLATE pg_catalog."default",
    baselinehepatitisc text COLLATE pg_catalog."default",
    interruptiontype character varying COLLATE pg_catalog."default",
    interruptionreason character varying COLLATE pg_catalog."default",
    interruptiondate date,
    hivstatusatprepinitiation text COLLATE pg_catalog."default",
    indicationforprep text COLLATE pg_catalog."default",
    currentregimen character varying COLLATE pg_catalog."default",
    currentduration integer,
    currentpreptype character varying COLLATE pg_catalog."default",
    currentprepdistributionsetting character varying COLLATE pg_catalog."default",
    dateoflastpickup date,
    currentsystolicbp double precision,
    currentdiastolicbp double precision,
    currentweight double precision,
    currentheight double precision,
    currenturinalysis text COLLATE pg_catalog."default",
    familyplanning character varying COLLATE pg_catalog."default",
    dateoffamilyplanning date,
    currenturinalysisdate date,
    currenthivstatus text COLLATE pg_catalog."default",
    dateofcurrenthivstatus date,
    pregnancystatus character varying COLLATE pg_catalog."default",
    currentstatus character varying COLLATE pg_catalog."default",
    dateofcurrentstatus date,
    period_start_date date,
    period_end_date date,
    ip_name character varying COLLATE pg_catalog."default"
) PARTITION BY LIST (period);

ALTER TABLE IF EXISTS hts_prep_datamart.final_prepquery_datamart
    OWNER to lamisplus_etl;

GRANT ALL ON TABLE hts_prep_datamart.final_prepquery_datamart TO lamisplus_etl;
-- Index: final_prep_periodtxt

-- DROP INDEX IF EXISTS hts_prep_datamart.final_prep_periodtxt;

CREATE INDEX IF NOT EXISTS final_prep_periodtxt
    ON hts_prep_datamart.final_prepquery_datamart USING btree
    (period COLLATE pg_catalog."default" ASC NULLS LAST)
;

-- Partitions SQL

CREATE TABLE hts_prep_datamart."final_quarterly_prep_202Q4" PARTITION OF hts_prep_datamart.final_prepquery_datamart
    FOR VALUES IN ('2024Q4')
TABLESPACE pg_default;
ALTER TABLE IF EXISTS hts_prep_datamart."final_quarterly_prep_202Q4"
    OWNER to lamisplus_etl;

CREATE TABLE hts_prep_datamart."final_quarterly_prep_202Q3" PARTITION OF hts_prep_datamart.final_prepquery_datamart
    FOR VALUES IN ('2024Q3')
TABLESPACE pg_default;
ALTER TABLE IF EXISTS hts_prep_datamart."final_quarterly_prep_202Q3"
    OWNER to lamisplus_etl;
	
CREATE TABLE hts_prep_datamart."final_quarterly_prep_202Q2" PARTITION OF hts_prep_datamart.final_prepquery_datamart
    FOR VALUES IN ('2024Q2')
TABLESPACE pg_default;

ALTER TABLE IF EXISTS hts_prep_datamart."final_quarterly_prep_202Q2"
    OWNER to lamisplus_etl;
	
CREATE TABLE hts_prep_datamart."final_quarterly_prep_202Q1" PARTITION OF hts_prep_datamart.final_prepquery_datamart
    FOR VALUES IN ('2024Q1')
TABLESPACE pg_default;

ALTER TABLE IF EXISTS hts_prep_datamart."final_quarterly_prep_202Q1"
    OWNER to lamisplus_etl;