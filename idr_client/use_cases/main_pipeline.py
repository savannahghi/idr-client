from typing import Tuple

from django import conf

import mysql.connector
from mysql.connector import Error

from idr_client import config
from idr_client.core import queries
from idr_client.core import Task
from idr_client.lib import SQLMetadata


class FetchMetadataFromServer(Task[str, Tuple[SQLMetadata, SQLMetadata]]):
    """Connect to the remote server and fetch metadata."""

    def execute(self, server_url: str) -> Tuple[SQLMetadata, SQLMetadata]:
        # TODO: Add implementation. Connect to the server and fetch the
        #  metadata that describes what needs to be extracted.
        ...


class CheckChangesFromETL(Task[SQLMetadata, bool]):
    """Check a KenyaETL table for changes."""

    def execute(self, an_input: SQLMetadata) -> bool:
        # TODO: Add implementation.
        ...


class RunExtraction(Task[SQLMetadata, object]):
    """Extract data from a database."""

    def execute(self, an_input: SQLMetadata) -> object:
        # TODO: Add implementation.
        connection = None
        return an_input.as_task().execute(connection)
    
    def _create_connection(self):
        try:
            connection_config_dict = {
                'user': config.db_user,
                'password': config.db_pwd,
                'host': config.db_host,
                'database': config.db_name,
                'raise_on_warnings': True,
                'use_pure': False,
                'autocommit': True,
                'pool_size': 5
                }    
            connection = mysql.connector.connect(**connection_config_dict)

            if connection.is_connected():
                cursor = connection.cursor()
                return cursor
        except Error as e:
            print("Error while connecting to DB", e)
            
    def __extract_etldata(self,query):
        cursor = self._create_connection()
        output=None
        try:
            cursor.execute(query)
            output = cursor.fetchall()
            return output
        except Error as err:
            print("Error extracting data ",err)
            
    def get_tables(self):
        results = self.__extract_etldata(queries.list_dbs)
        for result in results:
            print(result)
        

        
