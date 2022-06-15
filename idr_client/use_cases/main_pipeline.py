import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Tuple
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
from localStoragePy import localStoragePy
import sqlite3
from sqlite3 import Error

from idr_client import config
from idr_client.core import Task, static_queries
from idr_client.lib import SQLMetadata

# facility variables
facility_name: str = config.facility_name
mfl_code: str = config.mfl_code

# server variables
server_url: str = config.server_url
user_name: str = config.user_name
user_pwd: str = config.user_pwd

# client variables
etl_db_host: str = config.etl_db_host
db_port: str = config.db_port
etl_user: str = config.etl_user
etl_db_pwd: str = config.etl_db_pwd
etl_db_name: str = config.etl_db_name

default_date = datetime.fromtimestamp(0)

# default_date = datetime.fromisoformat("2021-12-12 00:00:00")

localStorage = localStoragePy('idr-client', 'json')


def logs_db_connection(db_file):
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)


sqlite_db_file = "idr_client/data/idr_client.db"


def create_logs_table():
    conn = logs_db_connection(sqlite_db_file)
    cursor = conn.cursor()
    cursor.execute(static_queries.create_etl_logs)
    conn.commit()
    cursor.close()


create_logs_table()


def connect_to_db():
    """Create database connection."""
    url = f"mysql+pymysql://{etl_user}:{etl_db_pwd}@{etl_db_host}:{db_port}/{etl_db_name}"
    engine = create_engine(url)
    return engine.connect()


def execute_query(query):
    connection = connect_to_db()
    with connection as con:
        result = con.execute(query)
        return result


def get_user_token(user, pwd):
    resp = requests.post(server_url + '/api/auth/login/', auth=HTTPBasicAuth(user, pwd))
    if resp.status_code == 200:
        token = resp.json()["token"]
        localStorage.setItem("token", token)
        return token
    exit("Error getting token. Check Username and Password.")


def get_last_etl_run_date():
    return default_date
    # conn = logs_db_connection(sqlite_db_file)
    # cursor = conn.cursor()
    # query_logs = cursor.execute(static_queries.get_last_etlrun_date)
    #
    # etl_last_run_date = query_logs.first()[0]
    # if etl_last_run_date is None:
    #     return default_date
    #     cursor.close()
    #     conn.close()
    # return etl_last_run_date


def count_created_or_recorded(last_run_date):
    count_modified_or_created_record = f'''
        SELECT COUNT(uuid) FROM {config.etl_db_name}.etl_cervical_cancer_screening rec 
        WHERE (rec.date_created > '{last_run_date}') OR (rec.date_last_modified > '{last_run_date}');
        '''
    count = execute_query(count_modified_or_created_record)
    return count.first()[0]


class CheckChangesFromETL(Task[SQLMetadata, bool]):
    """Check a KenyaETL table for changes."""

    def execute(self, an_input) -> bool:
        execute_query(static_queries.create_etl_logs)
        last_etl_run = get_last_etl_run_date()
        record_count = count_created_or_recorded(last_etl_run)
        if record_count > 0:
            return True
        return False


class FetchMetadataFromServer(Task[str, Tuple[SQLMetadata, SQLMetadata]]):
    """Connect to the remote server and fetch metadata."""

    def execute(self, etl_changed: bool) -> Tuple[SQLMetadata, SQLMetadata]:
        if etl_changed:
            token = get_user_token(user_name, user_pwd)
            response = requests.get(server_url + "/api/sql_data/sql_extract_metadata/",
                                    headers={'Authorization': 'Token ' + token})
            if response.status_code == 200:
                # print("RESULTS", response.json()['results'])
                metadata = response.json()['results'][0]
                query = metadata['sql_query']
                with open('idr_client/core/queries.py', 'w') as f:
                    f.write("from idr_client import config\n\n" + query)
                    from idr_client.core import queries
                return {'metadata_name': metadata['name'], 'metadata_id': metadata['id'], 'query': queries.extract_data}
            exit("Error getting metadata")
        exit("No change on etl since last run.\nExiting...")


class RunExtraction(Task[SQLMetadata, object]):
    """Extract data from a database."""
    '''
    - run raw query as fetched from the server,
    - run a filter against the result of the query. filter based on last_extract_date
    '''

    def execute(self, an_input: SQLMetadata) -> object:
        query = an_input['query']
        extracts = execute_query(query)
        last_run_date = get_last_etl_run_date()
        new_extracts = [r for r in extracts if (r['Date_Created'] > last_run_date)
                        or (r['Date_Last_Modified'] > last_run_date)]

        return {'metadata_name': an_input['metadata_name'], 'metadata_id': an_input['metadata_id'],
                'extracts': new_extracts}


class RunTransformation(Task[SQLMetadata, object]):
    """Transform the extracts."""

    def execute(self, an_input: SQLMetadata) -> object:
        df = pd.DataFrame(an_input)
        df.to_csv("idr_client/data/extracts.csv", index=False)

        chunks_folder = "idr_client/data/chunks/"

        def create_chunks():
            counter = 0
            for csv_chunk in pd.read_csv('idr_client/data/extracts.csv', chunksize=100):
                csv_chunk.to_csv(chunks_folder + "chunk_" + str(counter) + ".csv")
                counter += 1

        create_chunks()
        total = len(os.listdir(chunks_folder))

        return {'metadata_name': an_input['metadata_name'], 'metadata_id': an_input['metadata_id'],
                'chunks': total, 'chunks_folder': chunks_folder}


class TransmitData(Task[SQLMetadata, object]):
    """Transmit the transformed data"""
    '''
    - Should be atomic process where all data should be committed to server or none.
    - Only on successful transmission, insert a record to etl_extract_log else
    - Rollback the action
    '''

    def execute(self, an_input: SQLMetadata) -> object:
        data = {"org_unit_name": facility_name, "org_unit_code": mfl_code, "content_type": "text/csv",
                "chunks": an_input['chunks'], "extras": {}, "extract_metadata": an_input['metadata_id']}

        response = requests.post(server_url + "/api/sql_data/sql_upload_metadata/", data=data,
                                 headers={'Authorization': 'Token ' + localStorage.getItem("token")})
        if response.status_code == 201:
            print("success creating metadata.", response.status_code)
            output = response.json()
            chunk_index: int = 0
            for data in os.listdir("idr_client/data/chunks/"):
                path = an_input['chunks_folder'] + data
                metadata_id = output['id']
                chunk = {"chunk_index": chunk_index, "chunk_content": None, "upload_metadata": metadata_id}
                url_ext = f"/api/sql_data/sql_upload_metadata/{metadata_id}/start_chunk_upload/"

                # post chunks without chunk content
                response = requests.post(server_url + url_ext,
                                         json=chunk,
                                         headers={'Authorization': 'Token ' + localStorage.getItem("token")})
                print("success creating chunks.",data)
                if response.status_code == 201:
                    chunk_id = response.json()["id"]
                    edit_chunk_url = f"{server_url}/api/sql_data/sql_upload_chunks/{chunk_id}/"
                    chunk_file = {"chunk_content": open(path, 'rb')}
                    chunk_index += 1

                    # patch chunks with chunk content
                    res = requests.patch(edit_chunk_url, files=chunk_file,
                                         headers={'Authorization': 'Token ' + localStorage.getItem("token")})
                    if res.status_code == 200:
                        print("success adding chunks_content.", res.status_code)
                    else:
                        # TODO: retries here
                        ...
                        print("Do retries and error catching")

                else:
                    # TODO: retries here
                    pass
        print("do retries here. ")
        exit()
