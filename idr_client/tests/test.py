import os

import pytest
import requests
from localStoragePy import localStoragePy
from requests.auth import HTTPBasicAuth
from sqlalchemy import create_engine

from configs import config
from idr_client.use_cases import main_pipeline as mp
from idr_client.core import static_queries
from datetime import datetime

local_storage = localStoragePy("test_local", "json")


@pytest.fixture
def user_token(user, pwd):
    resp = requests.post(config.server_url + '/api/auth/login/', auth=HTTPBasicAuth(user, pwd))
    if resp.status_code == 200:
        token = resp.json()["token"]
        local_storage.setItem("token", token)
        yield token


@pytest.fixture
def setup_sqlite_db(tmpdir):
    """ Fixture to set up sqlite db connection """
    db_file = os.path.join(tmpdir.strpath, "test.db")
    conn = mp.sqlite_db_connection(db_file)
    yield conn


@pytest.fixture
def setup_mysql_db():
    """ Fixture to set up mysql db connection """
    url = f"mysql+pymysql://{config.etl_user}:{config.etl_db_pwd}@{config.etl_db_host}:{config.db_port}/{config.etl_db_name}"
    engine = create_engine(url)
    yield engine.connect()


def test_sqlite_connection(setup_sqlite_db):
    q = '''
    SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;
    '''
    assert len(list(mp.execute_sqlite_query(q))) >= 0


def test_mysql_connection(setup_mysql_db):
    q = '''
    show tables;
    '''
    assert len(list(mp.execute_mysql_query(q))) >= 0


@pytest.fixture
def get_last_etl_run_date():
    query_logs = mp.execute_sqlite_query(static_queries.get_last_etlrun_date)
    results = query_logs.fetchall()
    if len(results) < 1:
        yield mp.get_last_etl_run_date() == datetime.fromtimestamp(0)
    yield mp.get_last_etl_run_date() == str(*results[0])


def test_created_or_recorded(get_last_etl_run_date):
    assert mp.count_created_or_recorded(get_last_etl_run_date) >= 0
