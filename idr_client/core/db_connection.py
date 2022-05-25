import mysql.connector
from mysql.connector import Error

import queries

import os

db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pwd = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')


def extract_etldata(connection,query):
    cursor = connection.cursor()
    output=None
    try:
        cursor.execute(query)
        output = cursor.fetchall()
        return output
    except Error as err:
        print("Error extracting data ",err)
              
try:
    connection_config_dict = {
        'user': db_user,
        'password': db_pwd,
        'host': db_host,
        'database': db_name,
        'raise_on_warnings': True,
        'use_pure': False,
        'autocommit': True,
        'pool_size': 5
        }
    
    connection = mysql.connector.connect(**connection_config_dict)

    if connection.is_connected():
        cursor = connection.cursor()
        results = extract_etldata(connection, queries.list_dbs)
        for result in results:
            print(result)
              
except Error as e:
    print("Error while connecting to DB", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
        
       