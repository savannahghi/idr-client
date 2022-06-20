import os
import sys


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        print(f"Missing {name} env variable")
        sys.exit(1)
    return value


# Ensure the environment variables are set.

# Org unit
require_env('ORG_UNIT_NAME')
require_env('ORG_UNIT_CODE')

# Server configs
require_env('SERVER_URL')
require_env('USER_NAME')
require_env('USER_PWD')

# Client configs
require_env('DB_HOST')
require_env('DB_PORT')
require_env('DB_NAME')
require_env('DB_USER')
require_env('DB_PASSWORD')


