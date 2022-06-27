import glob
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any

import pandas as pd
import requests
from localStoragePy import localStoragePy
from requests.auth import HTTPBasicAuth
from sqlalchemy import create_engine

from idr_client.configs import config
from idr_client.core import Task, static_queries
from idr_client.lib import SQLMetadata

# facility variables
facility_name = config.facility_name
mfl_code = config.mfl_code

# server variables
server_url = config.server_url
user_name = config.user_name
user_pwd = config.user_pwd

# client variables
etl_db_host = config.etl_db_host
db_port = config.db_port
etl_user = config.etl_user
etl_db_pwd = config.etl_db_pwd
etl_db_name = config.etl_db_name

default_date = datetime.fromtimestamp(0)

# default_date = datetime.fromisoformat("2021-12-12 00:00:00")

localStorage = localStoragePy('idr-client', 'json')


def connect_to_sqlite_db():
    """ create a database connection to a SQLite database """
    sqlite_db_file = os.path.join("idr_client/data/idr_client.db")
    return sqlite3.connect(sqlite_db_file)


def connect_to_mysql_db():
    """Create database connection."""
    url = f"mysql+pymysql://{etl_user}:{etl_db_pwd}@{etl_db_host}:" \
          f"{db_port}/{etl_db_name}"
    engine = create_engine(url)
    return engine.connect()


def execute_sqlite_query(query):
    connection = connect_to_sqlite_db()
    with connection as cursor:
        cursor = cursor.cursor()
        query_output = cursor.execute(query)
        return query_output


def execute_mysql_query(query):
    connection = connect_to_mysql_db()
    with connection as con:
        result = con.execute(query)
        return result


def get_user_token(user, pwd):
    try:
        resp = requests.post(server_url + '/api/auth/login/',  # type: ignore
                             auth=HTTPBasicAuth(user, pwd),
                             timeout=60)
        resp.raise_for_status()
    except requests.exceptions.Timeout as e:
        print(str(e))
        return "Connection timeout."
    except requests.exceptions.ConnectionError as e:
        print(str(e))
        return "Connection error."
    except Exception as e:
        print(str(e))
        return "Other exceptions."
    else:
        if resp.status_code == 200:
            token = resp.json()["token"]
            localStorage.setItem("token", token)
            token = token
        else:
            token = "No token"
        return token


def get_last_etl_run_date():
    query_logs = execute_sqlite_query(static_queries.get_last_etlrun_date)
    results = query_logs.fetchall()
    # return default_date
    if len(results) < 1:
        return default_date
    return str(*results[0])


def count_created_or_recorded(last_run_date):
    count_modified_or_created_record = f'''
        SELECT COUNT(uuid) FROM {config.etl_db_name}.etl_cervical_cancer_screening rec # noqa
        WHERE rec.date_last_modified > '{last_run_date}';
        '''
    count = execute_mysql_query(count_modified_or_created_record)
    return count.first()[0]


class CheckChangesFromETL(Task[SQLMetadata, bool]):
    """Check a KenyaETL table for changes."""

    def execute(self, an_input) -> bool:
        execute_sqlite_query(static_queries.create_etl_logs)
        last_etl_run = get_last_etl_run_date()
        record_count = count_created_or_recorded(last_etl_run)
        if record_count > 0:
            return True
        return False


class FetchMetadataFromServer(Task[str, Any], object):
    """Connect to the remote server and fetch metadata."""

    def execute(self, etl_changed) -> Dict[str, Any]:
        if bool(etl_changed):
            token = get_user_token(user_name, user_pwd)
            response = requests.get(
                server_url +  # type: ignore
                "/api/sql_data/sql_extract_metadata/",
                headers={'Authorization': 'Token ' + token})
            if response.status_code == 200:
                metadata = response.json()['results'][0]
                query = metadata['sql_query']
                with open('idr_client/core/queries.py', 'w') as f:
                    f.write("from idr_client.configs import config\n"
                            "# flake8: noqa\n\n" + query)
                    from idr_client.core import queries
                return {'metadata_name': metadata['name'],
                        'metadata_id': metadata['id'],
                        'query': queries.extract_data}

            exit("Error getting metadata")
        exit("No change on etl since last run.\nExiting...")


class RunExtraction(Task[Dict[str, Any], object]):
    """Extract data from a database."""

    def execute(self, an_input: Dict[str, Any]) -> object:
        query = an_input['query']
        extracts = execute_mysql_query(query)
        last_run_date = get_last_etl_run_date()
        new_extracts = [r for r in extracts if r['Date_Last_Modified'] >
                        datetime.strptime(str(last_run_date),
                                          '%Y-%m-%d %H:%M:%S')]

        return {'metadata_name': an_input['metadata_name'],
                'metadata_id': an_input['metadata_id'],
                'extracts': new_extracts}


class RunTransformation(Task[Dict[str, Any], object]):
    """Transform the extracts."""

    def execute(self, an_input: Dict[str, Any]) -> object:
        df = pd.DataFrame(an_input)
        df.to_csv("idr_client/data/extracts.csv", index=False)

        chunks_folder = "idr_client/data/chunks/"

        def create_chunks():
            counter = 0
            for csv_chunk in pd.read_csv('idr_client/data/extracts.csv',
                                         chunksize=100):
                csv_chunk.to_csv(
                    chunks_folder + "chunk_" + str(counter) + ".csv")
                counter += 1

        create_chunks()
        chunks_count = len(os.listdir(chunks_folder))

        return {'metadata_name': an_input['metadata_name'],
                'metadata_id': an_input['metadata_id'],
                'chunks': chunks_count, 'chunks_folder': chunks_folder}


class TransmitData(Task[Dict[str, Any], None]):
    """Transmit the transformed data"""

    def execute(self, an_input: Dict[str, Any]) -> None:
        data = {"org_unit_name": facility_name, "org_unit_code": mfl_code,
                "content_type": "text/csv", "chunks": an_input['chunks'],
                "extras": {}, "extract_metadata": an_input['metadata_id']}

        response = requests.post(
            server_url + "/api/sql_data/sql_upload_metadata/",  # type: ignore
            data=data,
            headers={
                'Authorization': 'Token ' + localStorage.getItem("token")
                })

        if response.status_code != 201:
            raise RuntimeError(response.status_code, response.content)
        output = response.json()
        metadata_id = output['id']
        chunk_index: int = 0
        chunks_dir = "idr_client/data/chunks/"
        for data_path in glob.iglob(f'{chunks_dir}/*'):
            chunk = {"chunk_index": chunk_index, "chunk_content": None,
                     "upload_metadata": metadata_id}
            url_ext = f"/api/sql_data/sql_upload_metadata/{metadata_id}" \
                      f"/start_chunk_upload/"
            # post chunks without chunk content
            response = requests.post(
                server_url + url_ext,  # type: ignore
                json=chunk, headers={
                    'Authorization': 'Token ' +
                                     localStorage.getItem("token")})
            if response.status_code == 201:
                chunk_id = response.json()["id"]
                edit_chunk_url = \
                    f"{server_url}/api/sql_data/sql_upload_chunks/{chunk_id}/"
                chunk_file = {"chunk_content": open(data_path, 'rb')}
                chunk_index += 1
                # patch chunks with chunk content
                res = requests.patch(
                    edit_chunk_url, files=chunk_file,
                    headers={
                        'Authorization': 'Token ' +
                                         localStorage.getItem("token")})
                if res.status_code == 200:
                    print("success adding chunks_content.", res.status_code)
                else:
                    # TODO: retries here
                    ...
                    print("Do retries and error catching")
            else:
                # TODO: retries here
                pass

        def update_extraction_logs():
            metadata_name = an_input['metadata_name']
            query = f'''
            INSERT INTO tbl_extractions_log
            (metadata_id,metadata_name,extract_count)
            VALUES('{metadata_id}', '{metadata_name}', '{chunk_index}');
            '''
            execute_sqlite_query(query)

        update_extraction_logs()
        print("Success uploading chunks")
