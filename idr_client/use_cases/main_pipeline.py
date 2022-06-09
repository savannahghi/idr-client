import requests
from requests.auth import HTTPBasicAuth
from typing import Tuple
from datetime import datetime
from sqlalchemy import create_engine

from idr_client import config
from idr_client.core import Task,qries
from idr_client.lib import SQLMetadata


'''
- incremental FetchMetadataFromServer-
- tests and documentation
- packaging
- ansible playbook for deploy...deployment where no public IP consult kalume
- mvp (a deployed version)
- research on cli libs
'''

'''
### Flow
- Connect to etl_db
- Check etl_db for any changes. If changes:
- Establish connection to IDR_Server and get metadata
- Run extraction using metadata query
- Transform extracts
- Transmit
'''

# server environment variables
server_url: str = config.server_url
user_name: str = config.user_name
user_pwd: str = config.user_pwd

# client environment variables
etl_db_host:str = config.etl_db_host
db_port:str = config.db_port
etl_user:str = config.etl_user
etl_db_pwd:str = config.etl_db_pwd
etl_db_name:str = config.etl_db_name

default_date = datetime.fromtimestamp(0)


def connect_to_db():
    """Create database connection."""
    url = f"mysql+pymysql://{etl_user}:{etl_db_pwd}@{etl_db_host}:{db_port}/{etl_db_name}"
    try:
        engine = create_engine(url)
        return engine.connect()
    except Exception as e:
        raise e


def execute_query(query):
    connection = connect_to_db()
    with connection as con:
        result = con.execute(query)
        return result
    

def getLastETLRunDate():
    try:
        qry_logs = execute_query(qries.get_last_etlrun_date)
        etl_last_run_date = qry_logs['last_extract_datetime'][0]
        if not etl_last_run_date:
            etl_last_run_date = default_date
        return etl_last_run_date
    except Exception  as e:
        return default_date

def countEtlModifiedOrCreatedRecord():
    last_run_date = getLastETLRunDate()
    count_modified_or_created_record = f'''
        SELECT COUNT(uuid) FROM {config.etl_db_name}.etl_cervical_cancer_screening rec 
        WHERE (rec.date_created > '{last_run_date}') OR (rec.date_last_modified > '{last_run_date}');
        '''
    count = execute_query(count_modified_or_created_record)
    return count.first()[0]    
    
class CheckChangesFromETL(Task[SQLMetadata, bool]):
    """Check a KenyaETL table for changes."""
    def execute(self) -> bool:
        execute_query(qries.create_etl_logs)
        record_count = countEtlModifiedOrCreatedRecord()
        if record_count>0:
            return True
        return False
class FetchMetadataFromServer(Task[str, Tuple[SQLMetadata, SQLMetadata]]):
    """Connect to the remote server and fetch metadata."""

    def execute(self, etl_changed:bool) -> Tuple[SQLMetadata, SQLMetadata]:
        if etl_changed:
            resp = requests.post(server_url+'/api/auth/login/',auth = HTTPBasicAuth(user_name,user_pwd))
            if resp.status_code == 200:
                token = resp.json()["token"]
                response = requests.get(server_url+"/api/simple_sql_metadata/",headers={'Authorization': 'Token '+token})
                if response.status_code == 200:
                    metadata = response.json()['results'][0]
                    query = metadata['sql_query']
                    with open('idr_client/core/queries.py', 'w') as f:
                        f.write(query)
                        from idr_client.core import queries
                    return queries.extract_data
                raise Exception("Bad response ",response.status_code)
            raise Exception("No access token.",resp)
        raise Exception("No change on etl database")
                                
class RunExtraction(Task[SQLMetadata, object]):
    """Extract data from a database."""

    def execute(self, an_input: SQLMetadata) -> object: 
        results = execute_query(an_input)
        return results
        
class RunTransformation(Task[SQLMetadata, object]):
    """Transform the extracts."""
    def execute(self, an_input: SQLMetadata) -> object: 
        import pandas as pd
        df = pd.DataFrame(an_input)
        df.to_csv("extracts.csv",index=False)
        
        def write_parquet_file():
            df = pd.read_csv('extracts.csv')
            df.to_parquet('extracts.parquet')
            
        write_parquet_file()
        pq=pd.read_parquet("extracts.parquet")
        print(pq)
        
        
class TransimitData():
    """Transmit the transformed data"""
    ...
        
        