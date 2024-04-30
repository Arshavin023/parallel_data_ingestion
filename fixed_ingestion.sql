with duplicate_check as (
select file_name, facility_id, processed, ingest_error_message,ingest_end_time,
	row_number() over (partition by file_name order by modified_date desc) row_num
from public.sync_file
where facility_id in ('z6APuLTiHAX','FQ0Jc3pO5Op','DPA6BxE9pzQ','XyFDmlevgCu','RxLmSTf6Kpl',
'eJDSKTK7sO8','FxDuhc7a7mg','Ufkohku0hkU','rSLoHKc0nGd','sMllNyKolZf','gW4HoZwOJ9J','IiIYrVsq9rk',
'GBFvMIKcqNH','bQRrBX1dImc','sCJI7AumkSI','y9g73y2KvTz','x28h6GM4JaJ','zYDjpVGyR6R','Xb8UqZSE3u2',
'X1b3ELB9LTX','rSmFsJpZIM9','IU4lXhgmRYl','Jg82rXVgIjp','hxMSGzxlJoy','BVEHIFI2Fea','TqP0yUIXyDJ',
'konOEZuZo9H','sdO42TShMDc','mxeORAzNzal','ixltW74M2ch','MbdvhJg5Jag','eOrrK6aBIrt','BNvTkO5uvaN',
'NAGd5Q25uMa','QYEUyQCxByE','SoQeEge5A3R','NIulfQauxlQ','bz9lwL7ta7W','JZL6IMoe5G3','MuYD8OawdzS',
'wZTPrbae9ie','GU7GAjOSjpt','n2XQ6lwoh1F','hJnEYRxvSz2','nWMaBEIKXDv','f0J277xHATh','cmkm8UQpvWk')
and ingest_error_message not ilike '%UnicodeDecodeError - File is corrupted and unreadable, kindly regenerate and re-upload%'
--and ingest_error_message not ilike '%ProgrammingError - (UndefinedColumn) column%'
and processed in (2)
--order by modified_date desc;
)
select * from duplicate_check 
where processed = 2 and row_num > 1;


with duplicate_check as (
select file_name, facility_id, processed, ingest_error_message,ingest_end_time,
	row_number() over (partition by file_name order by modified_date desc) row_num
from public.sync_file
where file_name in ('hiv_status_tracker_46_20240418120711.json', 'patient_visit_28_20240419183840.json',
'hts_risk_stratification_1_20240422160610.json', 'triage_vital_sign_0_20240422191507.json',
'hts_client_0_20240422195215.json', 'hts_client_4_20240422160610.json', 
'mhpss_screening_0_20240416152629.json', 'biometric_0_20240416154512.json',
'hiv_art_pharmacy_1_20240416095228.json', 'hiv_observation_0_20240416154512.json')
--and ingest_error_message not ilike '%UnicodeDecodeError - File is corrupted and unreadable, kindly regenerate and re-upload%'
--and ingest_error_message not ilike '%ProgrammingError - (UndefinedColumn) column%'
and processed in (-2)
--order by modified_date desc;
)
select * from duplicate_check 
where processed = 2 and row_num > 1;