select * --delete 
from stg_hiv_art_pharmacy 
where stg_file_name in (select distinct file_name 
						from stg_monitoring
					   where processed='Y' and table_name = 'stg_hiv_art_pharmacy'
					   limit 3) limit 5



select file_name, table_name 
from stg_monitoring
where processed='Y'
limit 3