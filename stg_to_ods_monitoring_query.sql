(select 'successfully moved to ods' status, count(batch_id) 
 from public.stg_monitoring where processed='Y' and load_time >= '2024-07-15'
GROUP BY 1)
UNION ALL
(select 'yet to move to ods' status, count(batch_id) 
 from public.stg_monitoring where processed='N' and load_time >= '2024-07-15'
GROUP BY 1)
UNION ALL
(select 'failed to move to ods' status, count(batch_id) 
 from public.stg_monitoring where processed='F' and load_time >= '2024-07-15'
GROUP BY 1)

select * from public.stg_monitoring 
where processed='N' and load_time >= '2024-07-15' limit 5
AND file_name ilike '%biometric_118_20240816151653_decrypted.json%'
order by load_time



limit 25000

update public.stg_monitoring 
set processed='N' 
WHERE processed='F' 
AND error_message ilike '%Task received SIGTERM signal%'

select * from public.stg_monitoring
where processed='F' AND
--and error_message not ilike '%violates not-null constraint%'
table_name in ('stg_hiv_art_clinical') and load_time >= '2024-07-29' 
and load_time <= '2024-07-30'
order by load_time desc
limit 10
--datim_id in ('SEyGljwDspr') and 
--load_time >= '2024-08-14'
limit 3

--alter table  add column error_message character varying(200000);