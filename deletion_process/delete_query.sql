WITH CTE AS (
    SELECT file_name,
    ROW_NUMBER() OVER (PARTITION BY file_name ORDER BY json_rec_count) AS row_num
FROM public.sync_file WHERE processed = 1 and create_date >= '2024-03-21' 
AND NOT (decrypted_file_name ilike 'hiv_art_clinical%' or decrypted_file_name 
ilike 'dsd_devolvement%' or decrypted_file_name ilike 'mhpss_confirmation%'))
DELETE FROM public.sync_file
where file_name in (select file_name from CTE where row_num > 1);