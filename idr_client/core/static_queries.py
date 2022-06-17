# flake8: noqa

create_etl_logs = f'''
CREATE TABLE IF NOT EXISTS tbl_extractions_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metadata_id TEXT,
	metadata_name TEXT,
	extract_count INTEGER,
	last_extract_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

get_last_etlrun_date = f'''
SELECT MAX(last_extract_datetime) AS lastETLRunDate
FROM tbl_extractions_log;
'''
