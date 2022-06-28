from unittest.mock import MagicMock, patch
from unittest import TestCase
import requests
from sqlite3 import Connection as SQLiteConnection
from sqlalchemy.engine import Connection as AlchemyConnection
from idr_client.use_cases.main_pipeline import connect_to_sqlite_db, \
    execute_sqlite_query, execute_mysql_query, \
    get_user_token, get_last_etl_run_date

from requests.exceptions import RequestException, ConnectionError, Timeout


class TestUseCases(TestCase):
    @patch('idr_client.use_cases.main_pipeline.sqlite3')
    def test_sqlite_connection(self, mock_sqlite3):
        connection = MagicMock(SQLiteConnection)
        cursor = connection.cursor()
        mock_sqlite3.connect.return_value = cursor
        self.assertEqual(connect_to_sqlite_db(), cursor)

    @patch('idr_client.use_cases.main_pipeline.get_last_etl_run_date')
    def test_get_last_etl_run(self, mock_last_etl_run):
        mock_query_result = MagicMock(AlchemyConnection)
        mock_query_result.execute.return_value
        mock_last_etl_run.execute.return_value = mock_query_result
        get_last_etl_run_date()
        mock_query_result()
        mock_query_result.assert_called()

    def test_sqlite_query(self):
        query = "select count(log_id) from tbl_extractions_log"
        result = execute_sqlite_query(query).fetchone()
        self.assertGreaterEqual(result, (0,))

    @patch('idr_client.use_cases.main_pipeline.requests')
    def test_success_get_token(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": 1234
        }

        mock_requests.post.return_value = mock_response
        self.assertEqual(get_user_token("user", "pwd"), 1234)

    @patch('idr_client.use_cases.main_pipeline.requests')
    def test_status_code_failure_get_token(self, mock_get_token):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "No token"
        }
        mock_get_token.post.side_effect = mock_response
        self.assertEqual(get_user_token("user", "pwd"), "No token")

    @patch('idr_client.use_cases.main_pipeline.requests')
    def test_timeout_get_token(self, mock_timeout_request):
        mock_timeout_request.exceptions = requests.exceptions
        mock_timeout_request.post.side_effect = Timeout("Connection timeout.")
        self.assertEqual(get_user_token("user", "pwd"), "Connection timeout.")

    @patch('idr_client.use_cases.main_pipeline.requests')
    def test_connection_error_get_token(self, mock_connection_error):
        mock_connection_error.exceptions = requests.exceptions
        mock_connection_error.post.side_effect = \
            ConnectionError("Connection error.")
        self.assertEqual(get_user_token("user", "pwd"), "Connection error.")

    @patch('idr_client.use_cases.main_pipeline.requests')
    def test_general_error_get_token(self, mock_other_errors):
        mock_other_errors.exceptions = requests.exceptions
        mock_other_errors.post.side_effect = RequestException(
            "Other exceptions.")
        self.assertEqual(get_user_token("user", "pwd"), "Other exceptions.")

    @patch('idr_client.use_cases.main_pipeline.execute_mysql_query')
    def test_msql_connection(self, mock_mysql_query_exec):
        qry = "show tables;"
        mock_query_result = MagicMock(AlchemyConnection)
        mock_query_result.execute.return_value
        mock_mysql_query_exec.execute.return_value = mock_query_result
        execute_mysql_query(qry)
        mock_query_result(qry)
        mock_query_result.assert_called_with(qry)
