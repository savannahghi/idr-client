from idr_client import config

create_etl_logs = f'''
CREATE TABLE IF NOT EXISTS tbl_extraction_log (
	log_id INTEGER PRIMARY KEY,
	table_name TEXT,
	extracted_rowcount INTEGER,
	last_extract_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

get_last_etlrun_date = f'''
SELECT MAX(last_extract_datetime) AS lastETLRunDate
FROM tbl_extraction_log;
'''
