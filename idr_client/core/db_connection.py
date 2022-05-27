import mysql.connector
from mysql.connector import Error
import config
import queries

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
        
       