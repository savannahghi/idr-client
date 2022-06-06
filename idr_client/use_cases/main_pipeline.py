import requests
from typing import Tuple
import mysql.connector
from mysql.connector import Error

from idr_client import config
from idr_client.core import Task
from idr_client.lib import SQLMetadata

'''
### Flow
- Connect to etl_db
- Check etl_db for any changes. If changes:
- Establish connection to IDR_Server and get metadata
- Run extraction using metadata query
- Transform extracts
- Transmit
'''

# environment variables
server_url: str = config.server_url
etl_db_host:str = config.etl_db_host
etl_user:str = config.etl_user
etl_db_pwd:str = config.etl_db_pwd
etl_db_name:str = config.etl_db_name

def connect_to_etldb():
    try:
        connection_config_dict = {
            'user': etl_user,
            'password': etl_db_pwd,
            'host': etl_db_host,
            'database': etl_db_name,
            'raise_on_warnings': True,
            'use_pure': False,
            'autocommit': True,
            'pool_size': 5
            }    
        connection = mysql.connector.connect(**connection_config_dict)
        if connection.is_connected():
            return connection
    except Error as e:
        raise e  
    
def execute_query(query):
    connection = connect_to_etldb()
    cursor = connection.cursor()
    output=None
    try:
        cursor.execute(query)
        output = cursor.fetchall()
        connection.close()
        cursor.close()
        return output
    except Error as err:
        print("Error extracting data ",err)
            
class CheckChangesFromETL(Task[SQLMetadata, bool]):
    """Check a KenyaETL table for changes."""
    def execute(self,etl_db_host:str) -> bool:
        # TODO: Add implementation.
        ...
        return True


class FetchMetadataFromServer(Task[str, Tuple[SQLMetadata, SQLMetadata]]):
    """Connect to the remote server and fetch metadata."""

    def execute(self, etl_changed:bool) -> Tuple[SQLMetadata, SQLMetadata]:
        # TODO: Add implementation. Connect to the server and fetch the
        #  metadata that describes what needs to be extracted.
        
        # 1. Connect to the idr_server
        # 2. Return the metadata from idr_server
        if etl_changed:
            response = requests.get(server_url+"/api/simple_sql_metadata/")
            metadata = response.json()['results'][0]
            query = metadata['sql_query']
            return query
class RunExtraction(Task[SQLMetadata, object]):
    """Extract data from a database."""

    def execute(self, an_input: SQLMetadata) -> object: 
        results = execute_query(an_input)
        return results
        
class RunTransformation(Task[SQLMetadata, object]):
    """Extract data from a database."""

    def execute(self, an_input: SQLMetadata) -> object: 
        print("extractions ",an_input)
        
        