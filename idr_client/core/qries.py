from idr_client import config


create_etl_logs = f'''
CREATE TABLE IF NOT EXISTS {config.etl_db_name}.etl_extract_log
(
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    extracted_rowcount INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    end_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    last_extract_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_extracting BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT
);
'''

get_last_etlrun_date = f'''
SELECT MAX(last_extract_datetime) AS lastETLRunDate
FROM {config.etl_db_name}.etl_extract_log;
'''


