import os

# Server configs
server_url = os.getenv('SERVER_URL')
user_name = os.getenv('USER_NAME')
user_pwd = os.getenv('USER_PWD')

# Client configs
etl_db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
etl_db_name = os.getenv('DB_NAME')
etl_user = os.getenv('DB_USER')
etl_db_pwd = os.getenv('DB_PASSWORD')


