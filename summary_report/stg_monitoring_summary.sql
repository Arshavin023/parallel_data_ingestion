SELECT REPLACE(table_name,'stg_','') table_name, COUNT(file_name) unprocessed_files
FROM stg_monitoring
WHERE table_name NOT IN 
('stg_laboratory_sample_type','stg_laboratory_labtestgroup',
'stg_hiv_regimen_drug','stg_prep_regimen') 
AND load_time >= '2024-10-01'
AND datim_id NOT IN (SELECT datim_id FROM central_partner_mapping WHERE is_run)
AND processed='N' 
GROUP BY 1
ORDER BY COUNT(file_name) DESC;

SELECT *
FROM stg_monitoring
WHERE table_name='stg_sync_table_count' 
AND load_time >= '2024-10-01'
AND datim_id NOT IN (SELECT datim_id FROM central_partner_mapping WHERE is_run)
AND processed='F' 
ORDER BY load_time DESC
LIMIT 100;

UPDATE stg_monitoring SET processed='N'
WHERE table_name='stg_hiv_art_pharmacy' 
AND load_time >= '2024-10-01'
AND datim_id NOT IN (SELECT datim_id FROM central_partner_mapping WHERE is_run)
AND processed='F' 

SELECT REPLACE(table_name,'stg_','') table_name, COUNT(file_name) unprocessed_files
FROM stg_monitoring
WHERE table_name NOT IN 
('stg_laboratory_sample_type','stg_laboratory_labtestgroup',
'stg_hiv_regimen_drug','stg_prep_regimen') 
AND load_time >= '2024-10-25'
--AND datim_id IN (SELECT datim_id FROM central_partner_mapping WHERE ip_name IN ('SFH-KP-CARE 2','HAN-KP-CARE 1'))
AND processed='N' 
GROUP BY 1
ORDER BY COUNT(file_name) DESC;
--1362

SELECT DISTINCT ip_name FROM central_partner_mapping


SELECT REPLACE(table_name,'stg_','') table_name, COUNT(file_name) unprocessed_files
FROM stg_monitoring
WHERE table_name NOT IN 
('stg_laboratory_sample_type','stg_laboratory_labtestgroup',
'stg_hiv_regimen_drug','stg_prep_regimen') 
AND load_time >= '2024-11-20'
AND processed='F' 
GROUP BY 1
ORDER BY COUNT(file_name) DESC;

SELECT DISTINCT error_message 
FROM stg_monitoring 
WHERE processed='F' 
--AND table_name='stg_hiv_art_pharmacy_regimens'
ORDER BY load_time DESC
LIMIT 1000;

UPDATE stg_monitoring
SET processed='N' WHERE processed='F'
AND table_name IN ('stg_hiv_art_pharmacy_regimens')

SELECT * FROM stg_monitoring
WHERE processed='F'
AND table_name='stg_case_manager' 
-- AND load_time>='2024-11-14 14:50:00'
ORDER BY load_time DESC;

SELECT * FROM stg_monitoring
WHERE processed='Y'
AND table_name='stg_case_manager' 
-- AND load_time>='2024-11-14 14:50:00'
ORDER BY load_time DESC;

UPDATE stg_monitoring
SET processed='N'
WHERE processed='F' AND table_name='stg_case_manager';

SELECT DISTINCT error_message FROM stg_monitoring
WHERE processed='F'
AND table_name='stg_prep_clinic';

SELECT * FROM stg_monitoring
WHERE processed='Y'
AND table_name='stg_prep_eligibility'
AND load_time >= '2024-11-28';

SELECT * FROM stg_monitoring
WHERE processed='F'
AND table_name='stg_prep_eligibility';

UPDATE stg_monitoring
SET processed='N',error_message=null
WHERE processed='F'
AND table_name='stg_prep_eligibility';

SELECT * FROM stg_prep_clinic 
where stg_load_time >= '2024-11-26' 
and liver_function_test_results is not null
and liver_function_test_results!=null
limit 10;
