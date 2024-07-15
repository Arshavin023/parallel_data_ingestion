select * from public.sync_file where id=10
			
alter table public.sync_file add column ingest_error_message character varying

update public.sync_file
set csv_rec_count=0,ingest_status_check='processing',
ingest_error_message=null,processed=1,ingest_start_time=null
where id = 10

insert into public.sync_file (file_name,created_date,processed,ingest_status_check,csv_rec_count)
values('facility_test_updated.csv','2024-01-01',1,'processing',3000);
