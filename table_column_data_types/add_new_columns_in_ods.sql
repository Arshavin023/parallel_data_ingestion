ALTER TABLE ods_prep_clinic ADD COLUMN date_of_liver_function_test_results CHARACTER VARYING;
ALTER TABLE ods_hts_client ADD COLUMN accepted_pns CHARACTER VARYING;
ALTER TABLE ods_laboratory_test ADD COLUMN clinical_note CHARACTER VARYING;
ALTER TABLE ods_mhpss_screening ADD COLUMN facility_id BIGINT;
ALTER TABLE ods_patient_person ADD COLUMN latitude CHARACTER VARYING;
ALTER TABLE ods_case_manager ADD COLUMN password CHARACTER VARYING;
ALTER TABLE ods_prep_eligibility ADD COLUMN visit_type CHARACTER VARYING;
ALTER TABLE ods_hiv_art_clinical ADD COLUMN who CHARACTER VARYING;
ALTER TABLE ods_dsd_devolvement ADD COLUMN outlet_name CHARACTER VARYING;
ALTER TABLE ods_prep_clinic ADD COLUMN history_of_drug_allergies CHARACTER VARYING;
ALTER TABLE ods_hts_client ADD COLUMN referred_for_sti CHARACTER VARYING;
ALTER TABLE ods_prep_eligibility ADD COLUMN services_received_by_client JSONB;
ALTER TABLE ods_patient_person ADD COLUMN longitude CHARACTER VARYING;
ALTER TABLE ods_case_manager ADD COLUMN user_id CHARACTER VARYING;
ALTER TABLE ods_prep_clinic ADD COLUMN prep_type CHARACTER VARYING;
ALTER TABLE ods_hts_client ADD COLUMN offered_pns CHARACTER VARYING;
ALTER TABLE ods_prep_eligibility ADD COLUMN assessment_for_pep_indication JSONB;
ALTER TABLE ods_case_manager ADD COLUMN username CHARACTER VARYING;
ALTER TABLE ods_prep_clinic ADD COLUMN hiv_test_result_date DATE;
ALTER TABLE ods_hts_client ADD COLUMN comment CHARACTER VARYING;
ALTER TABLE ods_prep_eligibility ADD COLUMN assessment_for_prep_eligibility JSONB;
ALTER TABLE ods_prep_clinic ADD COLUMN population_type CHARACTER VARYING;
ALTER TABLE ods_prep_eligibility ADD COLUMN pregnancy_status CHARACTER VARYING;
ALTER TABLE ods_prep_clinic ADD COLUMN history_of_drug_to_drug_interaction character varying;
ALTER TABLE ods_prep_eligibility ADD COLUMN assessment_for_acute_hiv_infection JSONB;

ALTER TABLE ods_prep_clinic ADD COLUMN liver_function_test_result CHARACTER VARYING;
ALTER TABLE ods_prep_eligibility ADD COLUMN population_type CHARACTER VARYING;

ALTER TABLE ods_prep_clinic ADD COLUMN months_of_refill INTEGER;



--custom
ALTER TABLE ods_pmtct_mother_visitation ALTER COLUMN date_of_delivery TYPE CHARACTER VARYING USING date_of_delivery::CHARACTER VARYING;
--ALTER TABLE ods_pmtct_mother_visitation ALTER COLUMN date_of_delivery TYPE DATE USING date_of_delivery::DATE;
ALTER TABLE ods_prep_clinic ALTER COLUMN hiv_test_result_date TYPE CHARACTER VARYING USING hiv_test_result_date::CHARACTER VARYING;
--ALTER TABLE ods_prep_clinic ALTER COLUMN hiv_test_result_date TYPE DATE USING hiv_test_result_date::DATE;
ALTER TABLE ods_prep_clinic ALTER COLUMN months_of_refill TYPE CHARACTER VARYING USING months_of_refill::CHARACTER VARYING;
--ALTER TABLE ods_prep_clinic ALTER COLUMN months_of_refill TYPE INTEGER USING months_of_refill::INTEGER;
